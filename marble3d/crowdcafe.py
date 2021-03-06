import json
from django.conf import settings
from polygons import Polygon 
from shapes import getRectangleCoordinates, getPolygonPoints, getCanvasSize
import logging
import numpy
from PIL import Image, ImageDraw

from utils import splitArrayIntoPairs, getFileViaUrl, sendFileToDropbox
import random
import os
from models import Image as Img, Block

log = logging.getLogger(__name__)

# Bring judgement information from CrowdCafe into structure
class CrowdCafeJudgement:
	def __init__(self, crowdcafe_data):
		#log.debug('data: '+ str(shape_data))

		self.threashold = settings.MARBLE_3D_ERROR_THREASHOLD
		self.data = crowdcafe_data

		if '_shapes' in self.data['output_data']:
			shapes = json.loads(self.data['output_data']['_shapes'])
			for shape in shapes['objects']:
				if shape['type'] == 'image':
					self.canvas_size = getCanvasSize(shape)
				if shape['type'] == 'rect':
					self.polygon = Polygon(getRectangleCoordinates(shape))
				if shape['type'] == 'polygon':
					log.debug('shape - polygon')
					log.debug(shape)
					self.polygon = Polygon(getPolygonPoints(shape))
	def is_exist(self):
		if '_shapes' in self.data['output_data']:
			return True
		else:
			return False
	
	def makeCroppedImage(self, imagefile):
		# read image as RGB and add alpha (transparency)
		im = imagefile.convert("RGBA") #imagefile.convert("RGBA")
		# convert to numpy (for convenience)
		imArray = numpy.asarray(im)
		# create mask
		maskIm = Image.new('L', (imArray.shape[1], imArray.shape[0]), 0)
		#polygon_points = self.polygon.offset(settings.MARBLE_3D_ENLARGE_POLYGON)
		polygon_points = self.polygon.getSequence()
		log.debug(polygon_points)

		ImageDraw.Draw(maskIm).polygon(polygon_points, outline=1, fill=1)
		mask = numpy.array(maskIm)
		# assemble new image (uint8: 0-255)
		newImArray = numpy.empty(imArray.shape,dtype='uint8')
		# colors (three first columns, RGB)
		newImArray[:,:,:3] = imArray[:,:,:3]
		#transparency (4th column)
		newImArray[:,:,3] = mask*255

		# back to Image from numpy
		self.image = Image.fromarray(newImArray, "RGBA") #RGBA
		# Crop the image
		corners = self.polygon.getCorners()
		self.image = self.image.crop((corners[0]['x'], corners[0]['y'], corners[1]['x'], corners[1]['y']))
		# Create an image with green background and place image on it
		bg = Image.new("RGB", self.image.size, (0,255,0))
		bg.paste(self.image,self.image)
		self.image = bg
		
	def scalePolygon(self, imagefile):
		width, height = imagefile.size
		
		log.debug('polygon original:'+str(self.polygon.getPoints()))
		log.debug(width/self.canvas_size['width'],height/self.canvas_size['height']);
		
		# Scale according to image size
		self.polygon.scale(1.0*width/self.canvas_size['width'],1.0*height/self.canvas_size['height'])
		log.debug('polygon scaled:')
		log.debug(self.polygon.points)
		
		# Add margins
		self.polygon.enlargeAbs(settings.MARBLE_3D_ENLARGE_POLYGON)
		#self.polygon.offset(settings.MARBLE_3D_ENLARGE_POLYGON)
		log.debug('polygon enlarged:')
		log.debug(self.polygon.points)
		
		return self
	def cropAndSave(self, input_data, dropbox_token, dropbox_secret):
		log.debug('create a cropped image, based on the judgement'+str(self))
		# get image file from url
		imagefile = getFileViaUrl(input_data['url'])
		# bring polygon points to required tuple structure and enlarge it according to settings
		self.scalePolygon(imagefile)
		# get cropped image by polygon
		self.makeCroppedImage(imagefile)
		uploaded = sendFileToDropbox(self.image, input_data['block_title'], input_data['image_filename'], dropbox_token, dropbox_secret)

		log.debug('uploaded to dropbox: '+ str(uploaded))


# Compare pair of CrowdCafeJudgements
class Evaluation:
	def __init__(self, judgement1,judgement2, threashold):
		self.judgement1 = judgement1
		self.judgement2 = judgement2 # judgement2 is considered as gold in gold evaluation tasks
		self.threashold = threashold

		if self.judgement1.is_exist() and self.judgement2.is_exist():
			self.scale = self.getScale()
	def getScale(self):
		#TODO - do we need float here?
		scale = {
			'x' : float(self.judgement1.canvas_size['width'])/float(self.judgement2.canvas_size['width']),
			'y' : float(self.judgement1.canvas_size['height'])/float(self.judgement2.canvas_size['height'])
		}
		log.debug('scale: ' + str(scale))
		return scale

	# handle2 gold
	def judgementsAreSimilar(self):
		log.debug('\n **********************\n check judgements similarity')
		# if some of judgements are empty - return false
		if not self.judgement1.is_exist() or not self.judgement2.is_exist():
			return False
		evaluated = self.checkCentralPoint() and self.checkArea() and self.checkPerimeter()
		
		log.debug('\n judgements are similar to each other: '+ str(evaluated)+'\n**********************')
		
		return evaluated

	def checkCentralPoint(self): 
		
		central_points = {}
		central_points['judgement1'] = self.judgement1.polygon.getCenter()
		central_points['judgement2'] = self.judgement2.polygon.getCenter()

		delta_absolute = {
			'x':abs(central_points['judgement1']['x']/self.scale['x']-central_points['judgement2']['x']),
			'y':abs(central_points['judgement1']['y']/self.scale['y']-central_points['judgement2']['y'])
		}

		log.debug('central point delta absolute: ' + str(delta_absolute))
		
		judgement2_diagonal_length = self.judgement2.polygon.getAreaDiagonalLength()
		log.debug('polygon area diagonal length: '+ str(judgement2_diagonal_length))

		delta_relative = {
			'x': delta_absolute['x']/judgement2_diagonal_length,
			'y': delta_absolute['y']/judgement2_diagonal_length
		}

		log.debug('central point delta relative: ' + str(delta_relative))

		return delta_relative['x'] < self.threashold['center_distance'] and delta_relative['y']<self.threashold['center_distance']

	def checkArea(self):
		area1 = self.judgement1.polygon.getArea()
		area2 = self.judgement2.polygon.getArea()*(self.scale['x']*self.scale['y'])

		area_relative_difference = (max([area1,area2])-min([area1,area2]))/min([area1,area2])
		log.debug('area relative difference: ' + str(area_relative_difference))
		
		return area_relative_difference <= self.threashold['area']

	def checkPerimeter(self):
		per1 = self.judgement1.polygon.getPerimeter()
		per2 = self.judgement2.polygon.getPerimeter()*(self.scale['x'])
		
		perimetr_relative_difference = (max([per1,per2])-min([per1,per2]))/min([per1,per2])
		log.debug('perimetr relative difference: ' + str(perimetr_relative_difference))

		return  perimetr_relative_difference <= self.threashold['perimetr']

def controlCrowdCafeData(data_in_json):
	judgements = {}
	for item in data_in_json:
		if item['gold']:
			judgements['gold'] = CrowdCafeJudgement(crowdcafe_data = item)
		else:
			judgements['given'] = CrowdCafeJudgement(crowdcafe_data = item)
	evaluation = Evaluation(judgement1 = judgements['given'],judgement2 = judgements['gold'],threashold = settings.MARBLE_3D_ERROR_THREASHOLD)
	return evaluation.judgementsAreSimilar()