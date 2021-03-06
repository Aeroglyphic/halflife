from __future__ import print_function
import json, sys, datetime, re, csv, codecs, traceback, os
from pprint import pprint
from checkurl import *

if len(sys.argv) != 1 and len(sys.argv) != 4:
    print("usage: sample_scanner.py [<collection-key> <source-file-prefix> <sample-size>]")
    print("e.g. sample_scanner.py oukwa archive-sample/sample-of-1000/sample-for- 1000")
    sys.exit(1)

# Input filename template:
file_template = "archive-sample/sample-of-2000/ldwa"+datetime.datetime.now().strftime(".%Y.%m")+"-sample-for-%s.csv"
# output file prefix:
collection_key = "ldwa"
size = 2000
delim = ","
if len(sys.argv) != 1:
    collection_key = sys.argv[1]
    file_template = sys.argv[2]+"%s.csv"
    size = sys.argv[3]
    delim = "\t"

# Output filename template:
output_dir = datetime.datetime.now().strftime("sample-scan-results/%Y-%m-Explorer")
output_template = "%s/"+collection_key+"-sample-of-%s-scan-results.csv"
output_2_template = "%s/"+collection_key+"-sample-of-%s-scan-data.csv"


print("Using...")
print("    collection_key =",collection_key)
print("    file_template =",file_template)
print("    size =",size)
print("    output_dir =",output_dir)
print("    output_template =",output_template)
print("    output_2_template =",output_2_template)

# Loop over all sample sizes and check status:
url = "<none>"
if size != None:
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    out_file_2 = codecs.open( output_2_template % (output_dir, size), "w", "utf-8" )
    with codecs.open( output_template % (output_dir, size), "w", "utf-8") as out_file:
        for y in range(2004,2018):
            try:
                with open( file_template % y ) as data_file:
                    print("Processing year %s..." % y )
                    reader = csv.reader(data_file, delimiter=delim)
                    linc = 0
                    for row in reader:
                        linc = linc + 1
                        print("Scanning:",linc,row)
                        timestamp = datetime.datetime.strptime( row[0], "%Y-%m-%dT%H:%M:%SZ" )    
                        url = row[1]
                        title = row[2]
                        text_frag = row[3]
                        ssdeep = row[4]
                        md5 = row[5]


                        state = checkUrl( url )
                        status = state['status']
                        reason = state['reason']
                        key = mapStatusToKey( state )

                        # Also check content, if present:
                        identical = None
                        if state.has_key('md5'):
                            if state['md5'] == md5:
                                identical = True
                            else:
                                identical = False
                        # Similarity tactic:
                        similarity = None
                        if state.has_key('fh'):
                            similarity = fuzzyHashCompare(state['fh'], ssdeep)

                        # Also perform a soft-4xx check:
                        matchRandom = tryRandomUrlFor(state, url)
                        if matchRandom == True:
                            print("Found apparent soft-4xx!")
                            reason = "Soft 4xx"

                        # Clean up the reason:
                        try:
                            ascii_reason = reason.encode('ascii','replace')
                        except:
                            ascii_reason = "UNKNOWN REASON"         

                        month = timestamp.strftime("%m")
                        quarter = 1 + (int(month)-1)/3

                        # Default empty fields:
                        for tk in ['title','first_fragment','md5','fh','text']:
                            if not state.has_key(tk):
                                state[tk] = ''

                        try:
                            print( "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % ( y, quarter, month, key, status, ascii_reason, identical, similarity, url ), file=out_file )
                            url = "<done>"
                            out_file.flush()
                        except:
                            print("ERROR", y, url, key, status, ascii_reason)
                            traceback.print_exc()
                            sys.exit(1)

                        try: 
                            print( '"%s"\t"%s"\t"%s"\t"%s"\t"%s"\t"%s"\t"%s"' % ( "", url, state['title'], state['first_fragment'], state['fh'], state['md5'], state['text'] ), file=out_file_2 ) 
                            out_file_2.flush()
                        except:
                            print("ERROR", y, url, key, status, ascii_reason)
                            traceback.print_exc()

            except IOError as e: 
                print("Got IOError: "+str(e) + " when processing " + url)
                traceback.print_exc()
                
    out_file.close()
    out_file_2.close()
