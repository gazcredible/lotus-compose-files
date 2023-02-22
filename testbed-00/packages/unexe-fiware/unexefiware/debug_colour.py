colour_index = 0

colours = ['#C00000',
'#FF0000',
'#FFC000',
'#FFFF00',
#'#92D050',
#'#00B050',
'#00B0F0',
'#0070C0',
'#002060',
'#7030A0',
#'#FFFFFF',
'#000000',
#'#EEECE1',
'#1F497D',
'#4F81BD',
'#C0504D',
'#9BBB59',
'#8064A2',
'#4BACC6',
'#F79646',
#'#F2F2F2','#808080','#DDD9C4','#C5D9F1',
#'#DCE6F1','#F2DCDB','#EBF1DE','#E4DFEC',
#'#DAEEF3','#FDE9D9','#D9D9D9','#595959',
#'#C4BD97','#8DB4E2','#B8CCE4','#E6B8B7',
#'#D8E4BC','#CCC0DA','#B7DEE8','#FCD5B4',
#'#BFBFBF','#404040','#948A54','#538DD5',
#'#95B3D7','#DA9694','#C4D79B','#B1A0C7',
#'#92CDDC','#FABF8F','#A6A6A6','#262626',
#'#494529','#16365C','#366092','#963634',
#'#76933C','#60497A','#31869B','#E26B0A',
#'#808080','#0D0D0D','#1D1B10','#0F243E',
#'#244062','#632523','#4F6228','#403151',
#'#215967','#974706'
]

def get_colour():
    global colour_index
    global colours

    c = colours[colour_index]

    colour_index = colour_index + 1
    colour_index = colour_index % (len(colours) - 1)

    return c;