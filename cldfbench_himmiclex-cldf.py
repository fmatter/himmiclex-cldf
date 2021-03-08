import pathlib
import os
import csv
import random

from cldfbench import Dataset as BaseDataset

from cldflex import lift2cldf

import pseudo_words

lg_dic = {}

class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "himmiclex-cldf"
    
    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        from cldfbench import CLDFSpec
        return {
            "wordlist": CLDFSpec(dir=self.cldf_dir, module='Wordlist', data_fnames=dict(ParameterTable="meanings.csv")),
            "structure": CLDFSpec(dir=self.cldf_dir, module='StructureDataset')
        }

    def cmd_download(self, args):
        remap = {
            "bfz": "kotgarhi",
            "pnb": "pan" #file is erroneously tagged as eastern punjabi
        }
        for iso in open("etc/isos.txt").read().split("\n"):
            print(iso)
            if iso in remap:
                new = remap[iso]
            else:
                new = iso
            self.raw_dir.download("https://svn.spraakdata.gu.se/sb/IDS/pub/data-ids/ids-%s.csv" % new, 'ids-%s.csv' % iso)

    def cmd_makecldf(self, args):
        from csvw.dsv_dialects import Dialect
        
        himalayan_list = ["goe", "loy", "sip", "dzo", "xkz", "grt", "aeu", "dhi", "txo", "mxj", "lep", "lif", "thf", "blk", "cvg", "suv", "mla", "tan", "apt", "mhu", "clk", "duu"]
        
        lang_lits = {}
        for row in self.etc_dir.read_csv("links.csv", dicts=False):
            if row[0] not in lang_lits: lang_lits[row[0]] = []
            lang_lits[row[0]].append(row[1])

        def random_source(glottocode):
            lit = lang_lits[glottocode]
            ranlit = lit[random.randint(0,len(lit)-1)]
            ranpages = "[" + str(random.randint(0,150)) + "]"
            return ranlit + ranpages
            
        #initialize wordlist module
        with self.cldf_writer(args = None, cldf_spec = self.cldf_specs_dict["wordlist"]) as writer:
            writer.cldf.sources.add(*self.etc_dir.read_bib('himmiclex.bib'))
            writer.cldf.sources.add(*self.etc_dir.read_bib('glotto_refs.bib'))

            writer.cldf.add_component('LanguageTable')
            for lang in self.etc_dir.read_csv("languages.csv", dicts=True):
                writer.objects["LanguageTable"].append({"ID": lang["ID"], "Name": lang['Name'], "Glottocode": lang["Glottocode"], "Latitude": lang["Latitude"], "Longitude": lang["Longitude"]})
                lg_dic[lang["ID"]] = lang["Glottocode"]

            #In case cognates should be encoded at some point
            #writer.cldf.add_component('CognatesetTable')
            
            #Read in lexical data from https://spraakbanken.gu.se/projekt/digital-areal-linguistics
            skips = {"hin": 10, "kha": 10, "tel": 10, "ben": 9}
            orders = {
                1: ["ID", "Parameter", "Ortho", "Value", "Example"],
                2: ["ID", "Parameter", "Value", "Comment", "Example"],
                3: ["ID", "Parameter", "Value", "Example"],
                4: ["ID", "Parameter", "Ortho", "Value", "Comment", "Example"],
                5: ["ID", "Parameter", "Value", "Comment", "Example"],
            }
            table_orders = {
                "ben": 1,
                "bfz": 2,
                "bod": 3,
                "hin": 4,
                "kha": 5,
                "mar": 4,
                "nep": 3,
                "pnb": 3,
                "tam": 2,
                "tel": 2,
            }
            params = []
            for filename in os.listdir("raw"):
                if not filename.endswith(".csv") or "ids-" not in filename: continue
                iso = filename.split(".csv")[0].replace("ids-", "")
                max = 8
                if iso in skips:
                    max = skips[iso]
                for row in self.raw_dir.read_csv(
                        filename,
                        dicts=False,
                        dialect=Dialect(
                            skipRows=max,  # Ignore the citation info on top
                            skipBlankRows=True,
                            delimiter='\t',
                            header=False
                        )
                    ):
                        row = dict(zip(orders[table_orders[iso]], row))
                        if row["ID"] in ["S03.593"]: continue #double entry
                        if row["Value"] in ["-", "--", "", " "]: continue #empty entries
                        param_id = row['ID'].replace(".", "_")
                        #write values
                        writer.objects['FormTable'].append({
                                    "ID": iso + param_id,
                                    'Parameter_ID': row['ID'].replace(".", "_"),
                                    'Language_ID': iso,
                                    'Form': row['Value'].split(", ")[0],
                                    "Source": ["borin2013ids"]
                                })
                        # parameters (meanings) are constructed from value list
                        if param_id not in params:
                            params.append(param_id)
                            writer.objects["ParameterTable"].append({
                                "ID": param_id,
                                "Name": row["Parameter"]
                            })
                            
            added_entries = []
            
            #add example data for 'water' from csv file
            for row in self.etc_dir.read_csv("example_data.csv", dicts=True):
                writer.objects['FormTable'].append({
                    "ID": row["Language_ID"] + row['Parameter_ID'],
                    'Parameter_ID': row['Parameter_ID'],
                    'Language_ID': row["Language_ID"],
                    'Form': row['Value'],
                    "Source": [row["Source"] + "[" + row["Pages"] + "]"]
                })
                added_entries.append(row["Language_ID"] + row['Parameter_ID'])
                
            #add data from Puroik flex lift export
            lift2cldf.convert(
                lift_file = "raw/puroik/puroik.lift",
                lg_id="suv"
            )
            flex_maps = {}
            for mapping in self.etc_dir.read_csv("flex_maps.csv", dicts=True):
                flex_maps[mapping["Meaning"]] = mapping["ID"]
            for entry in csv.DictReader(open("raw/puroik/puroik_from_lift.csv")):
                param_id = flex_maps[entry["Meaning"]]
                writer.objects['FormTable'].append({
                            "ID": entry["Language_ID"] + param_id,
                            'Parameter_ID': param_id,
                            'Language_ID': entry["Language_ID"],
                            'Form': entry["Form"],
                            "Source": ["g:Lieberherr:Bulu-Puroik"]
                        })
                added_entries.append(entry["Language_ID"] + param_id)
                        
            #add some randomly generated words for the himalayan languages
            for param_id in params:
                for iso in himalayan_list:
                    if iso + param_id in added_entries: continue # real data already added above
                    writer.objects['FormTable'].append({
                                "ID": iso + param_id,
                                'Parameter_ID': param_id,
                                'Language_ID': iso,
                                'Form': pseudo_words.pseudo_word(),
                                "Source": [random_source(lg_dic[iso])]
                            })


        #put in some random data about classifiers
        with self.cldf_writer(args = None, cldf_spec = self.cldf_specs_dict["structure"], clean=False) as writer:
            writer.cldf.add_component('ParameterTable')
            writer.objects["ParameterTable"].append({
                    "ID": "cls",
                    "Name": "Classifiers",
                    "Description": "Are there nominal classifiers?"
                })
            writer.objects["ParameterTable"].append({
                    "ID": "cls_no",
                    "Name": "Order of classifiers, nouns, and numerals",
                    "Description": "What is the relative order of classifiers, nouns, and numerals?"
                })
            for lang in self.etc_dir.read_csv("languages.csv", dicts=True):
                if lang["ID"] in himalayan_list:
                    cl = pseudo_words.get_rand(["Yes", "No"])
                    writer.objects['ValueTable'].append({
                        "ID": lang["ID"] + "cls",
                        'Parameter_ID': "cls",
                        'Language_ID': lang["ID"],
                        'Value': cl,
                        "Source": [random_source(lg_dic[lang["ID"]])]
                    })
                    if cl == "Yes":
                        writer.objects['ValueTable'].append({
                            "ID": lang["ID"] + "cls_no",
                            'Parameter_ID': "cls_no",
                            'Language_ID': lang["ID"],
                            'Value': pseudo_words.get_rand(["N CL NUM", "CL N NUM", "NUM CL N", "CL NUM N", "NUM N CL", "N NUM CL"]),
                            "Source": [random_source(lg_dic[lang["ID"]])]
                        })
                    else:
                        writer.objects['ValueTable'].append({
                            "ID": lang["ID"] + "cls_no",
                            'Parameter_ID': "cls_no",
                            'Language_ID': lang["ID"],
                            'Value': "Not applicable",
                            "Source": [random_source(lg_dic[lang["ID"]])]
                        })