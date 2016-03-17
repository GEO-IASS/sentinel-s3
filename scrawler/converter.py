import re
from collections import OrderedDict
import xml.etree.cElementTree as etree


def camelcase_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_tiles_list(element):
    """ Returns the list of all tile names from Product_Organisation element
    in metadata.xml """

    tiles = {}

    for el in element:
        g = el.findall('.//Granules')[0]
        name = g.attrib['granuleIdentifier']

        name_parts = name.split('_')
        mgs = name_parts[-2]
        tiles[mgs] = name

    return tiles


def metadata_to_dict(metadata):
    """ Looks at metadata.xml file of sentinel product and extract useful keys
    Returns a python dict """

    tree = etree.parse(metadata)
    root = tree.getroot()

    meta = OrderedDict()

    keys = [
        'SPACECRAFT_NAME',
        'PRODUCT_STOP_TIME',
        'Cloud_Coverage_Assessment',
        'PROCESSING_LEVEL',
        'PRODUCT_TYPE',
        'PROCESSING_BASELINE',
        'SENSING_ORBIT_NUMBER',
        'SENSING_ORBIT_DIRECTION',
        'PRODUCT_FORMAT',
    ]

    # grab important keys from the file
    for key in keys:
        try:
            meta[key.lower()] = root.findall('.//' + key)[0].text
        except IndexError:
            meta[key.lower()] = None

    meta['product_cloud_coverage_assessment'] = float(meta.pop('cloud_coverage_assessment'))

    # get tile list
    meta['tiles'] = get_tiles_list(root.findall('.//Product_Organisation')[0])

    # get available bands
    bands = root.findall('.//Band_List')[0]
    meta['band_list'] = []
    for b in bands:
        meta['band_list'].append(b.text)

    return meta


def tile_metadata(tile, product):

    grid = 'T{0}{1}{2}'.format(tile['utmZone'], tile['latitudeBand'], tile['gridSquare'])

    meta = OrderedDict({
        'tile_name': product['tiles'][grid]
    })

    meta['date'] = tile['timestamp'].split('T')[0]

    # remove unnecessary keys
    product.pop('tiles')
    tile.pop('datastrip')
    bands = product.pop('band_list')

    for k, v in tile.iteritems():
        meta[camelcase_underscore(k)] = v

    meta.update(product)

    # construct download links
    links = ['http://sentinel-s2-l1c.s3.amazonaws.com/{0}/{1}.jp2'.format(meta['path'], b) for b in bands]

    meta['download_links'] = {
        'aws_s3': links
    }

    return meta


# if __name__ == '__main__':
#     product = metadata_to_dict('metadata.xml')

#     import json
#     f = open('tileInfo.json', 'r')
#     tile = json.loads(f.read(), object_pairs_hook=OrderedDict)

#     print(json.dumps(tile_metadata(tile, product)))