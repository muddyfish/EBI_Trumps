import json
import MySQLdb as sql
db = sql.connect("ensembldb.ensembl.org", "anonymous", port = 5306)
cur = db.cursor()

def getVersion():
    cur.execute("show databases like '%ensembl_production%'")
    return max([int(i[0].split("_")[2]) for i in cur.fetchall()])

def main():
    cur.execute('show databases like "%core_'+str(getVersion())+'_%";')
    species = [i[0] for i in cur.fetchall()]
    species_data = {}
    for s in species:
        species_name = s.split("_core_")[0]
        cur.execute("use "+s)
        cur.execute("select statistic, name, description, value from genome_statistics as gs, attrib_type as att where gs.attrib_type_id = att.attrib_type_id and (gs.attrib_type_id = 64 or gs.attrib_type_id = 405 or gs.attrib_type_id = 406 or gs.attrib_type_id = 403);")
        data = [list(i[1:]) for i in cur.fetchall()]
        species_data[species_name] = data
    return species_data

fileObj = open("species.json", "w")
json.dump(main(), fileObj)
fileObj.close()
