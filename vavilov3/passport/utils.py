
# 100)   Wild
# 	110)  Natural
# 	120)  Semi-natural/wild
# 	130)  Semi-natural/sown
# 200)    Weedy
# 300)    Traditional cultivar/landrace
# 400)    Breeding/research material
# 	410) Breeder's line
# 	411) Synthetic population
# 	412) Hybrid
# 	413) Founder stock/base population
# 	414) Inbred line (parent of hybrid cultivar)
# 	415) Segregating population
# 	416) Clonal selection
# 	420) Genetic stock
# 	421) Mutant (e.g. induced/insertion mutants, tilling populations)
# 	422) Cytogenetic stocks (e.g. chromosome addition/substitution, aneuploids, amphiploids)
# 	423) Other genetic stocks (e.g. mapping populations)
# 500) Advanced or improved cultivar (conventional breeding methods)
# 600) GMO (by genetic engineering)
# 999) Other (Elaborate in REMARKS field)

BIOLOGICAL_STATUS = {'Wild species': '100',
                     'Autotetraploid; Wild species': '100',
                     'Monogenic; Wild species': '100',
                     'Wild material': '100',
                     'Allozyme marker; Wild species': '100',
                     '100': '100',
                     '110': '110',
                     '120': '120',
                     '130': '130',
                     '300': '300',
                     '500': '500',
                     '410': '410',
                     '411': '411',
                     '412': '412',
                     '413': '413',
                     '414': '414',
                     '415': '415',
                     '420': '420',
                     '421': '421',
                     '422': '422',
                     '423': '423',
                     '200': '200',
                     '1': None,
                     '999': None,
                     'Autotetraploid': None,
                     '400': '400',
                     '10': None,
                     '415': '415',
                     '414': '414',
                     None: None,
                     'Genetic material': '400',
                     'Monogenic': '423',
                     'Misc markers': '423',
                     'Backcross recombinant inbred (L. pimp.)': '400',
                     'Cultivar': '300',
                     'Cultivar; Disease resistant': '300',
                     'Disease resistant; Monogenic': '300',
                     'Disease resistant; Misc markers': '300',
                     'Cultivar; Monogenic': '300',
                     'Landrace': '300',
                     'Breeding material': '400',
                     'Uncertain improvement status': None,
                     'Cultivated material': '300',
                     'Latin American cultivar': '300',
                     'Introgression line (S. habrochaites)': '423',
                     'Introgression line (S. lycopersicoides)': '423',
                     'Introgression line (S. pennellii)': '423',
                     'Allozyme marker; Introgression line (S. lycopersicoides); Monogenic': '423',
                     'Male sterile; Monogenic': '423',
                     'Provisional mutant': '421',
                     'Trisomic': '423',
                     'Chromosome marker': None,
                     'Allozyme marker; Monogenic': None,
                     'Misc markers; Monogenic': None,
                     'Alien substitution': None,
                     'Disease resistant': None,
                     'Chromosome marker; Monogenic': None,
                     }

# 10) Wild habitat
# 11) Forest or woodland
# 12) Shrubland
# 13) Grassland
# 14) Desert or tundra
# 15) Aquatic habitat
# 20) Farm or cultivated habitat
# 21) Field
# 22) Orchard
# 23) Backyard, kitchen or home garden (urban, periurban or rural)
# 24) Fallow land
# 25) Pasture
# 26) Farm store
# 27) Threshing floor
# 28) Park
# 30) Market or shop
# 40) Institute, Experimental statio n, R esearch organization, Genebank
# 50) Seed company
# 60) Weedy, disturbed or ruderal habitat
# 61) Roadside
# 62) Field margin
# 99) Other

HABITATS = {'30': '30',
            '31': '31',
            '21': '21',
            '22': '22',
            '23': '23',
            '24': '24',
            '25': '25',
            '26': '26',
            '27': '27',
            '28': '28',
            '10': '10',
            '11': '11',
            '12': '12',
            '13': '13',
            '23': '23',
            '24': '24',
            '61': '61',
            '26': '26',
            '40': '40',
            '50': '50',
            '20': '20',
            '62': '62',
            '60': '60',
            '14': '14',
            '15': '15',
            '99': '99'
            }

OLD_COUNTRIES = {'CSK': 'CSHH',
                 'YUG': 'YUCS',
                 'SUN': 'SUHH',  # URRS
                 'ZAR': 'COD',
                 'BYS': 'BLR',  # Biolorusia
                 'ANT': 'ANHH',
                 'Union of Soviet Socialist Republics': 'SUHH',
                 'Czechoslovakia': 'CSHH',
                 'Yugoslavia': 'YUCS',
                 'SCG': 'SRB',
                 'BUR': 'MMR'
                 }

COUNTRIES = {'YEMEN, REPUBLIC OF': 'YEMEN',
             'BOLIVIA': 'BOLIVIA, PLURINATIONAL STATE OF',
             'DEUTCHLAND': 'GERMANY',
             'DEUTSCHLAND': 'GERMANY',
             'RUSSIA': 'RUSSIAN FEDERATION',
             'ZAIRE': 'CONGO, DEMOCRATIC REPUBLIC OF THE',
             'BRASIL': 'BRAZIL',
             'PHILLIPINES': 'PHILIPPINES',
             'ENGLAND': 'UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND',
             'UNITED KINGDOM': 'UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND',
             'LIBANON': 'LEBANON',
             'CZECH REPUBLIC': 'CZECHIA',
             'MOLDOVA': 'MOLDOVA, REPUBLIC OF',
             'NDL': 'NETHERLANDS',
             'THE NEDERLANDS': 'NETHERLANDS',
             'BYS': None,
             'UNITED STATES OF AMERICA': 'UNITED STATES',
             'SAIPAN': 'UNITED STATES',
             'TANZANIA': 'TANZANIA, UNITED REPUBLIC OF',
             'YUGOSLAVIA': None,
             'YUG': None,
             'Venezuela': 'VENEZUELA, BOLIVARIAN REPUBLIC OF',
             'VENEZUELA': 'VENEZUELA, BOLIVARIAN REPUBLIC OF',
             'IRAN': 'IRAN, ISLAMIC REPUBLIC OF',
             'SYRIA': 'SYRIAN ARAB REPUBLIC',
             "C√¥TE D'IVOIRE": "CÔTE D'IVOIRE",
             'BYELORUSSIAN SSR (BELARUS)': 'BELARUS',
             'DDR': 'GERMANY',
             'SUN': None,
             'MACEDONIA': 'MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF',
             'S. AFRICA': 'SOUTH AFRICA',
             'THE NETHERLANDS': 'NETHERLANDS',
             'CONGO, THE DEMOCRATIC REPUBLIC': 'CONGO',
             'CONGO, THE DEMOCRATIC REPUBLIC OF THE': 'CONGO',
             "KOREA, DEMOCRATIC PEOPLE'S REPLUBLIC": "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF",
             'ROM': 'ROMANIA',
             'CSF': None, 'BKF': None, 'CNN': None, 'SSS': None, 'JUA': None,
             }
UKNOWN_COUNTRIES = {'BULGARIA/ITALY', 'UNKNOWN', 'FR. OCEANIA'}
