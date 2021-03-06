from lxml import etree
import argparse
from pymongo import MongoClient
import json
import xmltodict
import urllib

parser = argparse.ArgumentParser(description='Enter Your OAI Endpoint Information')
parser.add_argument("-u", "--url", dest="urlforoai", help="Specify your OAI endpoint")
parser.add_argument("-s", "--set", dest="oaiset", help="Specify your OAI set")
parser.add_argument("-m", "--metadata_prefix", dest="metadata_prefix", help="Specify metadata prefix", required=True)
parser.add_argument("-c", "--collection", dest="collection", help="Which collection?")
parser.add_argument("-mu", "--mongo_uri", dest="mongo_uri", help="Specifiy Mongouri", default="localhost")
args = parser.parse_args()

client = MongoClient(f'mongodb://{args.mongo_uri}:27017/')
db = client.dltndata


def check_endpoint(url):
    print(url)
    f = urllib.request.urlopen(url)
    s = f.read()
    document = etree.fromstring(s)
    error_code = document.findall('.//{http://www.openarchives.org/OAI/2.0/}error')
    if len(error_code) == 1:
        print("\nThere is something wrong with your OAI-PMH endpoint. Make sure your set or metadata format exists. "
              "For more information about your error, see this url:\n\n{0}\n".format(url))
    else:
        grab_oai(url, session_token, total_records)


def grab_oai(url, token, num_of_records):
    print(url + token)
    f = urllib.request.urlopen(url + token)
    s = f.read()
    clean = remove_other_bad_stuff(s)
    document = etree.fromstring(clean)
    new_session_token = document.findall('.//{http://www.openarchives.org/OAI/2.0/}resumptionToken')
    json_string = json.dumps(xmltodict.parse(clean))
    json_document = json.loads(json_string, object_hook=remove_dot)
    number_of_oai_records = len(json_document['OAI-PMH']['ListRecords']['record'])
    i = 0
    while i < number_of_oai_records:
        if 'metadata' in json_document['OAI-PMH']['ListRecords']['record'][i]:
            record_id = json_document['OAI-PMH']['ListRecords']['record'][i]['header']['identifier']
            metadata = json_document['OAI-PMH']['ListRecords']['record'][i]['metadata']
            result = mongocollection.update({"record_id": record_id},
                                            {"record_id": record_id, "oai_provider": oai_endpoint,
                                             "metadata": metadata}, True)
            num_of_records += 1
        i += 1
    print('\nRecord creation complete. Created or updated {0} records.\n'.format(num_of_records))
    if len(new_session_token) == 1:
        resumption_token = '&resumptionToken={0}'.format(new_session_token[0].text)
        if resumption_token != '&resumptionToken=None':
            grab_oai(oai_endpoint + "?verb=ListRecords", resumption_token, num_of_records)


def remove_dot(obj):
    for key in obj.keys():
        new_key = key.replace(".", "")
        if new_key != key:
            obj[new_key] = obj[key]
            del obj[key]
    return obj


def remove_other_bad_stuff(some_bytes):
    good_string = some_bytes.decode('utf-8')
    good_string = good_string.replace(u'\u000B', u'')
    good_string = good_string.replace(u'\u000C', u'')
    good_bytes = good_string.encode("utf-8")
    report = open('metadatadump.txt', 'w')
    report.write(good_string)
    report.close()
    return good_bytes

if __name__ == "__main__":
    # Defaults
    oai_endpoint = 'http://dpla.lib.utk.edu:8080/repox/OAIHandler'
    metadata_prefix = '&metadataPrefix='
    oai_set = session_token = ''
    num_publishers = total_records = 0
    collection = "default"

    if args.urlforoai:
        oai_endpoint = args.urlforoai
    if args.oaiset:
        oai_set = '&set=' + oai_set + args.oaiset
    if args.collection:
        collection = args.collection
    mongocollection = db[collection]
    metadata_prefix += args.metadata_prefix

    full_search_string = oai_endpoint + "?verb=ListRecords" + oai_set + metadata_prefix
    check_endpoint(full_search_string)
