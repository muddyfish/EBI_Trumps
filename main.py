from flask import Flask, request, redirect, render_template
import json

app = Flask(__name__)
app.debug = True
app.secret_key = "|&{FSf[.>;@\%x0PG'rvse>BHJuvxDXV[XciN(YC97-*Cdd[j~b/E!HKXu.i8k+YmcuygHKOxS6)bcno<<sm`ITZu%^xR;QXX9/{R#V^n^.{;'C$<[S=wGDf1]q?m50jRk!."
fileObj = open("species.json")
species = json.load(fileObj)
fileObj.close()

def getImageName(species_name):
    return "http://static.ensembl.org/i/species/64/" + species_name.capitalize() + ".png"

def getCardData(filename, id):
    id = int(id)
    species_name = species.keys()[id]
    for i, value in enumerate(species[species_name]):
        if value[1].find("ength of the") != -1:
            species[species_name][i][2] = "{:10.1f} Gb".format(value[2]/float(1000000000))
    card_data = [species_name.replace("_", " ").title(), getImageName(species_name), species[species_name], id]
    return render_template(filename, text_height=2, h_gap=0.1, inner_width=17.8, card_data=card_data)

@app.route("/htmlcard")
def htmlcard():
    return getCardData("htmlcard.html", int(request.args["id"]))
@app.route("/card")
def card():
    return getCardData("card.html", int(request.args["id"]))

@app.route("/buttonsubmit", methods=["POST"])
def buttonSubmit():
    print request.form["button"]
    return "Success!"

@app.route("/")
def root():
    return render_template("index.html")

if __name__ == "__main__":
    app.run("0.0.0.0")