from flask import Flask, request, redirect, render_template, session, send_file, url_for, send_from_directory
import json, random, copy, StringIO, string, time

def getYN(text): #Get the answer to a yes or no question
    response = ""
    while response not in ["Y", "N"]:
        response = raw_input(text+"\t").upper()
    return response == "Y"

def getUniversalSettings(): #Get the settings for the program
    try:
        fileObj = open("settings.json")
        contents = json.load(fileObj)
        fileObj.close()
    except (IOError, ValueError), e:
        if e.__class__ is ValueError and not getYN("There is an error in your settings.json file. Recreate it?"): #If you don't, exit
            sys.exit()            
        else:
            print "Recreating settings.json"
        contents = {"secret": ''.join([random.SystemRandom().choice("{}{}{}".format(string.ascii_letters, string.digits, string.punctuation)) for i in range(100)]), \
                        "debug": False, \
                        "url": "0.0.0.0", \
                        "species": "species.json",
                    "cuteness": "cuteness.json"}
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

try:
    import numpy, Image #Not required for core
except ImportError:
    print "Numpy and PIL not found. Try installing them for nicer card errors."
else:
    @app.route("/error") #On the /error page 
    def getErrorImage(): #Create a random image
        imarray = numpy.random.rand(64, 64, 3) * 255 # 64x64 rgb image
        im = Image.fromarray(imarray.astype('uint8')).convert('RGB')
        output = StringIO.StringIO()
        im.save(output, format="PNG")
        output.seek(0)
        return send_file(output, mimetype='image/png')

def getCuteness():
    fileObj = open(contents["cuteness"])
    cuteness = json.load(fileObj)
    fileObj.close()
    return cuteness

def getError(e): #Get the card data from error messages
    return [e.__class__.__name__, "error", [["", "Error!", e.message]], 555, "MissingNo"] #Error name, image location, catagories, card id, splash text

def usesGigaBases(value): #Does the catagory in question use Gigabases?
    return value[1].find("ength of the") != -1

def usesDate(value):
    return value[1].find("Date") != -1

def getImageName(species_name): #Get the image URL given the species name
    return url_for('static', filename='images/%s.png'%(species_name))

def getCardData(filename, id): #Get the card data for a card with the given template and id.
    try:
        id = int(id)
        species_name = sorted(species.keys())[id]
    except (ValueError, IndexError), e: #Get the correct error message
        card_data = getError(e)
    else:
        localspecies = copy.deepcopy(species[species_name]["catagories"]) #Pointers...
        localspeciessplash =  copy.deepcopy(species[species_name]["image_splash"]) #Again...
        for i, value in enumerate(localspecies):
            localspecies[i].append(value[2])
            if usesGigaBases(value): #If useing gigabases, format them correctly
                localspecies[i][2] = "{:10.1f} Gb".format(value[2]/float(1000000000))
            elif usesDate(value):
                localspecies[i][2] = time.strftime("%b %Y", time.gmtime(-value[2]))
        card_data = [[species[species_name]["common"], species_name.replace("_", " ").title()], getImageName(species_name), localspecies, species_name]
    return render_template(filename, card_data=card_data, image_splash = localspeciessplash)

@app.route("/card") #On /card
def card():
    return getCardData("card.html", request.args["id"])

@app.route("/buttonsubmit", methods=["POST"])
def buttonSubmit(): #When a button is pressed
    turn = request.form["turn"] #Who's turn is it?
    chosen = request.form["button"].split("_")[1:] #Get the card id that was chosen
    chosen = ["_".join(chosen[:-1]), int(chosen[-1])-1]
    catagories = [species[sorted(species.keys())[card]]["catagories"][chosen[1]][2] for card in session['cards']]
    aiturn = catagories.index(max(catagories)) #Which card won?
    aimove = None
    won = session['cards'][aiturn] #Who won?
    session['deck'+str(catagories.index(max(catagories))+1)].extend(session['cards']) #Winners deck gets both cards.
    try:
        del session['deck1'][0] #Remove top card of both decks
        del session['deck2'][0]
    except IndexError: pass #Empty? don't care.
    if not (len(session['deck1']) == 0 or len(session['deck2']) == 0): #Are they empty now?
        session['cards'][0] = session['deck1'][0] #Set displayed cards to top card
        session['cards'][1] = session['deck2'][0]
        if aiturn: 
            keys = sorted(species.keys())
            aicard = species[keys[session['cards'][1]]]["catagories"] #Get the ai's card
            chosen = sorted(aicard, key = lambda x: x[3])[-1] #Sort the catagories by what's best
            for i in range(len(species[keys[session['cards'][1]]]["catagories"])):
                if species[keys[session['cards'][1]]]["catagories"][i] == chosen: #Always choose what is best
                    aimove = i
    output = StringIO.StringIO()
    output.write(json.dumps({"cardids": session['cards'], "won": won, "aiturn": bool(aiturn), "aimove": aimove, "maxcards": len(species.keys()), "cards": len(session['deck1'])})) #Return json
    output.seek(0)
    return send_file(output, mimetype='text/plain')


@app.route('/im/<path:filename>') #on /im/<image path here>
def base_static(filename):
    return send_from_directory(app.static_folder + '/images/', filename)

@app.route("/vote_cute")
def vote_cute():
    cuteness = getCuteness()
    index = random.randrange(len(cuteness)-1)
    return render_template("vote_cute.html", index=index)

@app.route("/cute_card")
def cute_card():
    try:
        index = int(request.args["index"])
        option = int(request.args["option"])
        index += option
        cuteness = getCuteness()
        species_name = cuteness[index]
    except (ValueError, TypeError): return ""
    return '<img style="width:17.8em; height:17.8em;" border="0" src="%s" onclick="onClick(%s)">'%(getImageName(species_name), index)

@app.route("/about")
def about(): #An about page
    return render_template("about.html")

@app.route("/new_game")
def new_game(): #Delete all cookies and redirect to root
    for i in dict(session).keys(): del session[i]
    return redirect(url_for('root', region=None, ip=None))

@app.route("/")
def root():
    if not session.has_key('deck1'): #If there isn't a deck1, recreate every cookie
        deck = range(len(species))
        random.shuffle(deck)
        session['deck1'] = deck[:len(deck)/2]
        session['deck2'] = deck[len(deck)/2:]
        session['cards'] = [session['deck1'][0], session['deck2'][0]]
    cards = session['cards']
    return render_template("index.html", cards = cards)

if __name__ == "__main__":
    app.run(contents["url"])
