from specifics import *
import wap          #import the Wolfram|Alpha API file
import praw         #import the PRAW file
import cirpy        #import the python wraper for the CIR
import time         #need time for some soft query delay


def handleword(word):
    #compare the word (to lower) to the chem list
    if word.lower() in chemlist:
        #if we've already failed the word
        if word in failedlist:
            print word+" is in my failed list... not trying it again"
            mention.reply('I\'m pretty sure '+word+' is either a chemical compound or a portion of what you ment but I wasn\'t able to find a CAS number for it.\n\nIf this is a problem, please '+footerGen(mention.permalink))
            return 0
        #This is a new or unfailed word
        else:
            print "Resolving "+word
            #Look up the CAS number, smiles and formula of the compound from CIR
            cas_num = cirpy.resolve(word,'cas')
            smiles = cirpy.resolve(word,'smiles')
            formula = cirpy.resolve(word,'formula')
            #The chemical is defined if we have at least one CAS number
            if cas_num:
                #Some compounds may have multiple CAS numbers so we want to handle the grammar
                isare = " is"
                if len(cas_num) > 1:
                    isare = "s are"
                if len(cas_num[0])>1:
                    #Build the WebBoook links and the list for multiple CAS numbers
                    formattedcas = ', '.join(cas_num)
                    link = ""
                    for cas in cas_num:
                        link = link+"["+cas+"](http://webbook.nist.gov/cgi/cbook.cgi?ID="+cas+"&Units=SI) "
                else:
                    #Build the WebBoook link and the list for one CAS number
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
                #See Wolfram|Alpha API docs for descriptions of pods
                for pod in pods:
                    if str(pod[1][1]) == "Structure diagram":
                        structureimage = pod[6][3][1][1]
                    if str(pod[1][1]) == "Basic properties":
                        propertiesimage = pod[6][3][1][1]
                        propertiestext = pod[6][3][5][1]
                #Build the reply
                mention.reply('How about some more info on '+word+':\n\nThe CAS number'+isare+' '+formattedcas+'\n\nThe chemical structure is '+smiles+'\n\nChemical formula: '+formula+'\n\nNIST WebBook '+link+'.\n\n\nThe following is from Wolfram|Alpha:\n\n[structure image]('+structureimage+')\n\n[basic properties image]('+propertiesimage+')\n\nBasic properties: '+propertiestext+'\n\n\n\nProvided by your friendly neighborhood Chemistry_Bot\n\n'+footerGen(mention.permalink))
                #Add the mention ot the already done set
                already_done.add(mention.id)
                print "Success on "+word
                #Add the mention to the commented on file
                with open("commentedonchem.txt", "a") as commentedfile:
                    commentedfile.write(mention.id+'\n')
                return 1
            else:
                #If a chemical was in our list but didn't resolve in the CIR we record it in the failed file
                print "Failure on "+word
                with open("failedat.txt","a") as failedat:
                    failedat.write(word+'\n')
                mention.reply('I\'m pretty sure '+word+' is either a chemical compound or a portion of what you ment but I wasn\'t able to find a CAS number for it.\n\nIf this is a problem, please '+footerGen(mention.permalink))
                return 0
    else:
        #The word is not in our chemlist
        print word+' not in my list'
        return 0

def footerGen(permalink):
    return '[report a mistake](http://www.reddit.com/message/compose/?to=Chemistry_Bot&subject=Error%20Report&message='+permalink+')'

#Connect to reddit
r = praw.Reddit('ChemBot v2.0 by u/chpwssn. Responds to username mentions with information on chemical compounds listed in the comment.')
r.login(botuser,botpass)

#Create sets to keep track of the mentions we've handled already
already_done = set()
done_this_time = set()

#Open the chemlist file, used to compare the words in a mention to a list of known compounds
with open("/root/chemlistfinal") as f:
    chemlist = f.read().splitlines()
#Convert the chemlist to all lowercase words
chemlist = [x.lower() for x in chemlist]
#Open the file used to keep track of the mentions we've already replied to
with open("commentedonchem.txt") as commentfile:
    prevmentions = commentfile.read().splitlines()
#Open the file used to keep track of the mentions we've already scanned for words
with open("chembotscanned.txt") as scannedfile:
    scanned = scannedfile.read().splitlines()
#Open the file for the words in the chemlist that we were unable to resolve
with open("failedat.txt") as failedatfile:
    failedlist = failedatfile.read().splitlines()
#Print the previous mentions to the console to keep track
print prevmentions
print scanned
#The looper variable is used in case we don't want to use an infinite loop
looper = True
#Keeping track of how many loops we've done
loops = 0

#Start while loop
while looper:
    loops += 1
    if loops%50 == 0:
        print 'Loop number: '+str(loops)+' I have done '+str(len(done_this_time))+': '+str(done_this_time)
    #Get the username mentions we have in our inbox
    mentions = r.get_mentions()
    for mention in mentions:
        #If we haven't scanned the mention yet previously or in this time running the script
        if mention.id not in scanned and mention.id not in done_this_time:
            #Record the mention as scanned in the file and the set
            with open("chembotscanned.txt", "a") as scannedfile:
                scannedfile.write(mention.id+'\n')
                done_this_time.add(mention.id)
            print mention
            print mention.id
            words = mention.body.split()
            chems_in_mention = 0
            #For each word in the mention
            for word in words:
                chems_in_mention += handleword(word)
            #For each word pair in the mention
            for i in xrange(0,len(words)-1,1):
                two_word = words[i]+' '+words[i+1]
                chems_in_mention += handleword(two_word)
            #We didn't find a compound we recognized in the mention comment so we want to reply with an appology
            if chems_in_mention == 0:
                mention.reply('Sorry, I was unable to find any valid chemicals in your comment, my list is rather small now but it will grow in the future!\n\nOnce I get a full list I will try again.\n\n'+footerGen(mention.permalink))
    #Simple rate limiting
    time.sleep(1)
    #end while loop
