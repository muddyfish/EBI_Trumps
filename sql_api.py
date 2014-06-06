import json
import urllib2
import MySQLdb as sql
db = sql.connect("ensembldb.ensembl.org", "anonymous", port = 5306) #Connect to ensembl sql server
cur = db.cursor()

def getVersion(): #Get the most up to date version of ensembl
    cur.execute("show databases like '%ensembl_production%'")
    return max([int(i[0].split("_")[2]) for i in cur.fetchall()])

def addAI(species_data): #Sort the catagories and add an order of the best moves
    values = [sorted([[i[0], i[1][2]] for i in zip(species_data.keys(), catagory)], key=lambda x: x[1]) for catagory in zip(*[species_data[i]["catagories"] for i in species_data.keys()])]
    for catagoryi, catagory in enumerate(values):
        for cardi, card in enumerate(catagory):
#            print card[1], cardi
            species_data[card[0]]["catagories"][catagoryi].append(cardi)
    return species_data

def addSounds(version, species_name): #Get the sounds that the animal makes from the plugin repro
    data = urllib2.urlopen("https://raw.githubusercontent.com/Ensembl/public-plugins/release/"+ str(version) +"/ensembl/conf/ini-files/" + species_name.capitalize() + ".ini") #Get the correct url
    try: #Does it have a sound?
        noise = data.read().split("ENSEMBL_SOUND")[1].split("=")[1][1:-1] #Get the sound
    except IndexError:
        noise = "" #No sound...
    return noise

def main(): #Start!
    version = getVersion()
    cur.execute('show databases like "%core_'+str(version)+'_%";') #Get all species
    species = [i[0] for i in cur.fetchall()] #Fetch them
    species_data = {}
    for s in species:
        species_name = s.split("_core_")[0] #Get the species name
        print "Getting data for species:", species_name
        cur.execute("use "+s) #Use the table
        cur.execute("select statistic, name, description, value from genome_statistics as gs, attrib_type as att where gs.attrib_type_id = att.attrib_type_id and (gs.attrib_type_id = 64 or gs.attrib_type_id = 405 or gs.attrib_type_id = 406 or gs.attrib_type_id = 403);") #If you want more catagories, extend this to include the attribute types you want
        data = sorted([list(i[1:]) for i in cur.fetchall()])
#        print data
        species_data[species_name] = {}
        species_data[species_name]["catagories"] = data
        species_data[species_name]["image_splash"] = addSounds(version, species_name)
    return species_data

fileObj = open("species.json", "w")
json.dump(addAI(main()), fileObj)
fileObj.close()
