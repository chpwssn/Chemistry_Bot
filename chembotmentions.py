from specifics import *
import wap
import praw
import cirpy
import time

r = praw.Reddit('ChemBot v2.0 by u/chpwssn')
r.login(botuser,botpass)
already_done = set()
done_this_time = set()
with open("/root/chemlistfinal") as f:
    chemlist = f.read().splitlines()
chemlist = [x.lower() for x in chemlist]
with open("commentedonchem.txt") as commentfile:
    prevmentions = commentfile.read().splitlines()
with open("chembotscanned.txt") as scannedfile:
    scanned = scannedfile.read().splitlines()
with open("failedat.txt") as failedatfile:
    failedlist = failedatfile.read().splitlines()
print prevmentions
print scanned
looper = True
loops = 0
while looper:
    loops += 1
    if loops%50 == 0:
        print 'Loop number: '+str(loops)+' I did '+str(done_this_time)
    mentions = r.get_mentions()
    for mention in mentions:
        if mention.id not in scanned and mention.id not in done_this_time:
            with open("chembotscanned.txt", "a") as scannedfile:
                scannedfile.write(mention.id+'\n')
                done_this_time.add(mention.id)
            for chem in chemlist:
                if chem in mention.body and mention.id not in scanned and mention.id not in already_done and mention.id not in prevmentions:
                    print mention
                    print mention.id
                    words = mention.body.split()
                    chems_in_mention = 0
                    for word in words:
                        if word.lower() in chemlist:
                            chems_in_mention += 1
                            if word in failedlist:
                                print word+" is in my failed list... not trying it again"
                            else:
                                print "Resolving "+word
                                cas_num = cirpy.resolve(word,'cas')
                                smiles = cirpy.resolve(word,'smiles')
                                formula = cirpy.resolve(word,'formula')
                                if cas_num:
                                    isare = " is"
                                    if len(cas_num) > 1:
                                        isare = "s are"
                                    if len(cas_num[0])>1:
                                        formattedcas = ', '.join(cas_num)
                                        link = ""
                                        for cas in cas_num:
                                            link = link+"["+cas+"](http://webbook.nist.gov/cgi/cbook.cgi?ID="+cas+"&Units=SI) "
                                    else:
                                        formattedcas = cas_num
                                        link = ""
                                        link = link+"["+cas_num+"](http://webbook.nist.gov/cgi/cbook.cgi?ID="+cas_num+"&Units=SI)"
                                    #wolfram portion of the query
                                    waeo = wap.WolframAlphaEngine(appid, server)
                                    query = waeo.CreateQuery(word)
                                    result = waeo.PerformQuery(query)
                                    waeqr = wap.WolframAlphaQueryResult(result)
                                    pods = waeqr.Pods()
                                    structureimage =""
                                    propertiesimage=""
                                    propertiestext=""
                                    for pod in pods:
                                        if str(pod[1][1]) == "Structure diagram":
                                            structureimage = pod[6][3][1][1]
                                        if str(pod[1][1]) == "Basic properties":
                                            propertiesimage = pod[6][3][1][1]
                                            propertiestext = pod[6][3][5][1]
                                    mention.reply('How about some more info on '+word+':\n\nThe CAS number'+isare+' '+formattedcas+'\n\nThe chemical structure is '+smiles+'\n\nChemical formula: '+formula+'\n\nNIST WebBook '+link+'.\n\n\nThe following is from Wolfram|Alpha:\n\n[structure image]('+structureimage+')\n\n[basic properties image]('+propertiesimage+')\n\nBasic properties: '+propertiestext+'\n\n\nProvided by your friendly neighborhood Chemistry_Bot\n\n[report an error](http://redd.it/1wwur4)')
                                    already_done.add(mention.id)
                                    print "Success on "+word
                                    with open("commentedonchem.txt", "a") as commentedfile:
                                        commentedfile.write(mention.id+'\n')
                                else:
                                    print "Failure on "+word
                                    with open("failedat.txt","a") as failedat:
                                        failedat.write(word+'\n')
                        else:
                            print word+' not in my list'
            if chems_in_mention == 0:
                mention.reply('Sorry, I was unable to find any valid chemicals in your comment, my list is rather small now but it will grow in the future!\n\nOnce I get a full list I will try again.\n\n[report an error](http://redd.it/1wwur4)') 
    time.sleep(1)
