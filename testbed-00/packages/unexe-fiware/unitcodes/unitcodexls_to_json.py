import openpyxl
import json

#http://wiki.goodrelations-vocabulary.org/Documentation/UN/CEFACT_Common_Codes

if __name__ == '__main__':
    wb = openpyxl.load_workbook(filename = 'unitcodes/rec20_Rev9e_2014.xlsx')
    ws = wb['Annex I']

    lookup = {}

    isFirstRow = True
    for row in ws.values:
        if isFirstRow == False:
            lookup[row[6]] = str(row[9])
        else:
            isFirstRow = False

    with open('unexefiware/unitcodes.json', 'w') as f:
        json.dump(lookup, f)


#A:Group Number B:Sector C:Group ID D:Quantity E:Level/ Category F:Status G:Common Code H:Name I:Conversion Factor J:Symbol K:Description
#A:01 B:Space and Time C:2 D:angle (plane) E:1 G:C81 H:radian I:rad J:rad
