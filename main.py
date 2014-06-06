from flask import Flask, request, redirect, render_template, session, send_file, url_for, send_from_directory
import json, random, copy
import numpy, Image, StringIO

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

@app.route("/error")
def getErrorImage():
    imarray = numpy.random.rand(64, 64, 3) * 255
    im = Image.fromarray(imarray.astype('uint8')).convert('RGB')
    output = StringIO.StringIO()
    im.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype='image/png')

def getError(e):
    return [e.__class__.__name__, "error", [["", "Error!", e.message]], 555, "MissingNo"]

def usesGigaBases(value):
    return value[1].find("ength of the") != -1

def getImageName(species_name):
    return "http://static.ensembl.org/i/species/64/" + species_name.capitalize() + ".png"

def getCardData(filename, id):
    try:
        id = int(id)
        species_name = species.keys()[id]
    except (ValueError, IndexError), e:
        card_data = getError(e)
    else:
        localspecies = copy.deepcopy(species[species_name]["catagories"])
        localspeciessplash =  copy.deepcopy(species[species_name]["image_splash"])
        for i, value in enumerate(localspecies):
            localspecies[i].append(value[2])
            if usesGigaBases(value):
                localspecies[i][2] = "{:10.1f} Gb".format(value[2]/float(1000000000))
        card_data = [species_name.replace("_", " ").title(), getImageName(species_name), localspecies, id]
    return render_template(filename, card_data=card_data, image_splash = localspeciessplash)

@app.route("/cardback")
def cardback():
    return render_template("cardback.html")

@app.route("/htmlcard")
def htmlcard():
    return getCardData("htmlcard.html", request.args["id"])
@app.route("/card")
def card():
    return getCardData("card.html", request.args["id"])

@app.route("/buttonsubmit", methods=["POST"])
def buttonSubmit():
    turn = request.form["turn"]
    chosen = [int(i) for i in request.form["button"].split("_")[1:]]
    chosen[1]-=1
    catagories = [species[species.keys()[session['cards'][0]]]["catagories"][chosen[1]][2], \
                  species[species.keys()[session['cards'][1]]]["catagories"][chosen[1]][2]]
    aiturn = catagories.index(max(catagories))
    aimove = None
    won = session['cards'][aiturn]
    session['deck'+str(catagories.index(max(catagories))+1)].extend(session['cards'])
    try:
        del session['deck1'][0]
        del session['deck2'][0]
    except IndexError: pass
    if not (len(session['deck1']) == 0 or len(session['deck2']) == 0):
        session['cards'][0] = session['deck1'][0]
        session['cards'][1] = session['deck2'][0]
        if aiturn:
            aicard = species[species.keys()[session['cards'][1]]]["catagories"]
            chosen = sorted(aicard, key = lambda x: x[3])[-1]
            keys = species.keys()
            for i in range(len(species[keys[session['cards'][1]]]["catagories"])):
                if species[keys[session['cards'][1]]]["catagories"][i] == chosen:
                    aimove = i
    output = StringIO.StringIO()
    output.write(json.dumps({"cardids": session['cards'], "won": won, "aiturn": bool(aiturn), "aimove": aimove, "maxcards": len(species.keys()), "cards": len(session['deck1'])}))
    output.seek(0)
    return send_file(output, mimetype='text/plain')


@app.route('/im/<path:filename>')
def base_static(filename):
    return send_from_directory(app.static_folder + '/images/', filename)


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/new_game")
def new_game():
    for i in dict(session).keys(): del session[i]
    return redirect(url_for('root', region=None, ip=None))

@app.route("/")
def root():
    if not session.has_key('deck1'):
        deck = range(len(species))
        random.shuffle(deck)
        session['deck1'] = deck[:len(deck)/2]
        session['deck2'] = deck[len(deck)/2:]
        session['cards'] = [session['deck1'][0], session['deck2'][0]]
    cards = session['cards']
    return render_template("index.html", cards = cards)

if __name__ == "__main__":
    app.run(contents["url"])
