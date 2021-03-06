"""
This file is the test case for the marble3d.
"""
from django.contrib.auth.models import User
from django.test import TestCase
import logging

import numpy
import json

from utils import splitArrayIntoPairs, CrowdCafeCall
from django.conf import settings
from crowdcafe import CrowdCafeJudgement, Evaluation, controlCrowdCafeData
from tasks import processCrowdCafeResult,processGoodJudgement
from polygons import Polygon

log = logging.getLogger(__name__)

class Marble3D(TestCase):
    '''
    testing the marble3d tasks
    '''
    def setUp(self):
        '''
        setup the enviroment
        '''
        self.polygon_judgement = {'output_data': {u'_shapes': u'{"objects":[{"type":"image","originX":"left","originY":"top","left":0,"top":0,"width":1410,"height":793,"fill":"rgb(0,0,0)","stroke":null,"strokeWidth":1,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":1,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","src":"http://www.ucarecdn.com/3097f45a-b049-4acc-90dd-cb0862b90768/-/resize/600x/","filters":[],"crossOrigin":""},{"type":"polygon","originX":"left","originY":"top","left":628,"top":765,"width":1,"height":1,"fill":"green","stroke":"blue","strokeWidth":5,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":0.5,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","points":[{"x":-0.5,"y":-0.5},{"x":0.5,"y":-0.5},{"x":-334,"y":-261},{"x":-384,"y":-541},{"x":-381,"y":-699},{"x":4,"y":-717},{"x":197,"y":-737},{"x":637,"y":-687},{"x":564,"y":-355},{"x":101,"y":-53}]}],"background":""}'}, 'score': 0.0, 'unit': 622, 'pk': 1325, 'gold': False};
        self.polygon_data_incorrect = [{'output_data': {u'_shapes': u'{"objects":[{"type":"image","originX":"left","originY":"top","left":0,"top":0,"width":1250,"height":704,"fill":"rgb(0,0,0)","stroke":null,"strokeWidth":1,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":1,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","src":"http://www.ucarecdn.com/92918193-322a-4f05-8935-abba458bb588/-/resize/600x/","filters":[],"crossOrigin":""},{"type":"polygon","originX":"left","originY":"top","left":379,"top":218,"width":1,"height":1,"fill":"green","stroke":"blue","strokeWidth":5,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":0.5,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","points":[{"x":-0.5,"y":-0.5},{"x":253,"y":-60},{"x":406,"y":96},{"x":172,"y":159},{"x":114,"y":477}]}],"background":""}'}, 'score': 0.0, 'unit': 207, 'pk': 212, 'gold': False}, {'output_data': {u'_shapes': u'{"objects":[{"type":"image","originX":"left","originY":"top","left":0,"top":0,"width":1250,"height":704,"fill":"rgb(0,0,0)","stroke":null,"strokeWidth":1,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":1,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","src":"http://www.ucarecdn.com/92918193-322a-4f05-8935-abba458bb588/-/resize/600x/","filters":[],"crossOrigin":""},{"type":"polygon","originX":"left","originY":"top","left":360,"top":137,"width":1,"height":1,"fill":"green","stroke":"blue","strokeWidth":5,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":0.5,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","points":[{"x":-0.5,"y":-0.5},{"x":73,"y":-73},{"x":274,"y":-85},{"x":618,"y":-29},{"x":623,"y":-15},{"x":584,"y":277},{"x":275,"y":468},{"x":235,"y":465},{"x":209,"y":453},{"x":19,"y":361},{"x":9,"y":335},{"x":-3,"y":128}]}],"background":""}'}, 'score': 1.0, 'unit': 207, 'pk': 203, 'gold': True}]
        self.polygon_data_correct   = [{'output_data': {u'_shapes': u'{"objects":[{"type":"image","originX":"left","originY":"top","left":0,"top":0,"width":1250,"height":704,"fill":"rgb(0,0,0)","stroke":null,"strokeWidth":1,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":1,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","src":"http://www.ucarecdn.com/92918193-322a-4f05-8935-abba458bb588/-/resize/600x/","filters":[],"crossOrigin":""},{"type":"polygon","originX":"left","originY":"top","left":342,"top":143,"width":1,"height":1,"fill":"green","stroke":"blue","strokeWidth":5,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":0.5,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","points":[{"x":-0.5,"y":-0.5},{"x":86,"y":-85},{"x":297,"y":-100},{"x":655,"y":-41},{"x":619,"y":291},{"x":299,"y":486},{"x":-10,"y":336}]}],"background":""}'}, 'score': 0.0, 'unit': 207, 'pk': None, 'gold': False}, {'output_data': {u'_shapes': u'{"objects":[{"type":"image","originX":"left","originY":"top","left":0,"top":0,"width":1250,"height":704,"fill":"rgb(0,0,0)","stroke":null,"strokeWidth":1,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":1,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","src":"http://www.ucarecdn.com/92918193-322a-4f05-8935-abba458bb588/-/resize/600x/","filters":[],"crossOrigin":""},{"type":"polygon","originX":"left","originY":"top","left":360,"top":137,"width":1,"height":1,"fill":"green","stroke":"blue","strokeWidth":5,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":0.5,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","points":[{"x":-0.5,"y":-0.5},{"x":73,"y":-73},{"x":274,"y":-85},{"x":618,"y":-29},{"x":623,"y":-15},{"x":584,"y":277},{"x":275,"y":468},{"x":235,"y":465},{"x":209,"y":453},{"x":19,"y":361},{"x":9,"y":335},{"x":-3,"y":128}]}],"background":""}'}, 'score': 1.0, 'unit': 207, 'pk': 203, 'gold': True}]
        
        #self.judgements = [{'output_data': {u'_shapes': u'{"objects":[{"type":"image","originX":"left","originY":"top","left":0,"top":0,"width":1250,"height":704,"fill":"rgb(0,0,0)","stroke":null,"strokeWidth":1,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":1,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","src":"http://www.ucarecdn.com/48aa063d-9589-4631-96cf-00c3effc2e5f/-/resize/600x/","filters":[],"crossOrigin":""},{"type":"polygon","originX":"left","originY":"top","left":282,"top":206,"width":1,"height":1,"fill":"green","stroke":"blue","strokeWidth":5,"strokeDashArray":null,"strokeLineCap":"butt","strokeLineJoin":"miter","strokeMiterLimit":10,"scaleX":1,"scaleY":1,"angle":0,"flipX":false,"flipY":false,"opacity":0.5,"shadow":null,"visible":true,"clipTo":null,"backgroundColor":"","points":[{"x":-0.5,"y":-0.5},{"x":16,"y":-73},{"x":34,"y":-109},{"x":116,"y":-140},{"x":147,"y":-135},{"x":729,"y":-55},{"x":673,"y":292},{"x":162,"y":436},{"x":2,"y":288}]}],"background":""}'}, 'score': 0.0, 'unit': 174, 'pk': 201, 'gold': False}]    
    def test_evaluation_incorrect(self):
        evaluation = controlCrowdCafeData(self.polygon_data_incorrect)
        self.assertEqual(evaluation, False)

    def test_evaluation_correct(self):
        evaluation = controlCrowdCafeData(self.polygon_data_correct)
        self.assertEqual(evaluation, True)
    
    def test_polygon_enlargement(self):
        polygon = Polygon([{'x':10,'y':10},{'x':20,'y':10},{'x':20,'y':20},{'x':10,'y':20}])
        polygon_enlarged = Polygon([{'y': 9.75, 'x': 9.75}, {'y': 9.75, 'x': 20.25}, {'y': 20.25, 'x': 20.25}, {'y': 20.25, 'x': 9.75}])
        
        self.assertEqual(polygon.enlargeRel(1.05).points, polygon_enlarged.points)
    
    def test_cropAndSave(self):
        item = self.polygon_judgement
        unit_url = settings.CROWDCAFE['api_url']
        unit_url+= 'unit/'+str(item['unit'])+'/'

        calls = CrowdCafeCall()
        unit = calls.sendRequest('get',unit_url).json()

        
        url = settings.CROWDCAFE['api_url']+'unit/'+str(item['unit'])+'/judgement/'
        judgements_of_unit = calls.sendRequest('get',url).json()
        
        log.debug('judgements in the unit are: ' + str(judgements_of_unit['count']))

        judgement_to_pick = CrowdCafeJudgement(crowdcafe_data = item)
        
        secret = 'DROPBOX_USER_SECRET'
        token = 'DROPBOX_USER_TOKEN'
        # create cropped image based on the selected judgement and send to dropbox
        judgement_to_pick.cropAndSave(unit['input_data'],token,secret)
