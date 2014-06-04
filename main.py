from flask import Flask, request, redirect, render_template, session
import json, random, string, sys

def getYN(text):
    response = ""
    while response not in ["Y", "N"]:
        response = raw_input(text+"\t").upper()
    return response == "Y"

def getUniversalSettings():
    try:
        fileObj = open("settings.json")
        contents = json.load(fileObj)
        fileObj.close()
    except (IOError, ValueError), e:
        if e.__class__.__name__ == "ValueError" and not getYN("There is an error in your settings.json file. Recreate it?"):
            sys.exit()            
        else:
            print "Recreating settings.json"
        contents = {"secret": ''.join([random.SystemRandom().choice("{}{}{}".format(string.ascii_letters, string.digits, string.punctuation)) for i in range(100)]), \
                        "debug": True, \
                        "url": "0.0.0.0", \
                        "species": "species.json"}
        fileObj = open("settings.json", "w")
        json.dump(contents, fileObj)
        fileObj.close()
    return contents

contents = getUniversalSettings()
app = Flask(__name__)
app.debug = contents["debug"]
app.secret_key = contents["secret"]
fileObj = open(contents["species"])
species = json.load(fileObj)
fileObj.close()

def getError(e):
    return [e.__class__.__name__, "error", [["", "Error!", e.message]], 555]

def getImageName(species_name):
    return "http://static.ensembl.org/i/species/64/" + species_name.capitalize() + ".png"

def getCardData(filename, id):
    try:
        id = int(id)
        species_name = species.keys()[id]
    except (ValueError, IndexError), e:
        card_data = getError(e)
    else:
        for i, value in enumerate(species[species_name]):
            if value[1].find("ength of the") != -1:
                species[species_name][i][2] = "{:10.1f} Gb".format(value[2]/float(1000000000))
        card_data = [species_name.replace("_", " ").title(), getImageName(species_name), species[species_name], id]
    return render_template(filename, text_height=2, h_gap=0.1, inner_width=17.8, card_data=card_data)

@app.route("/htmlcard")
def htmlcard():
    return getCardData("htmlcard.html", request.args["id"])
@app.route("/card")
def card():
    return getCardData("card.html", request.args["id"])

@app.route("/buttonsubmit", methods=["POST"])
def buttonSubmit():
    print request.form["button"]
    return "Success!"

@app.route("/")
def root():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(contents["url"])
