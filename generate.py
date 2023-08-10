from bs4 import BeautifulSoup

from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
import textwrap

import fitz
  
import os


## CONFIG
dir_path = os.path.dirname(os.path.realpath(__file__))
template = '_template.pdf'
template_extra = '_template_extra.pdf'

sources = ['FightClub5eXML/Sources/PlayersHandbook/spells-phb.xml',
           'FightClub5eXML/Sources/XanatharsGuideToEverything/spells-xge.xml']

read_spells(spells,'')
read_spells(spells,'spells-phb.xml')

descriptionrect_a = fitz.Rect(12, 116.5, 168, 239.5)
descriptionrect_b = fitz.Rect(12, 17, 168, 230)  
titlerect = fitz.Rect(10, 6.8, 173, 20)
subtitlerect = fitz.Rect(10, 105.3, 173, 120)  


#####################################
## Condition spell text for front and back sides of cards
## Limitation: currently fit for 1x _template.pdf 
##                           and 2x _template_extra.pdf
##
## Input:   Spell-list with 1 long string in 'text'
## Process: Split 'text' if too long for a single card
## Output:  Spell-list with 1-3 strings in 'text' list
#####################################
def condition_text(spell):
    testdoc = fitz.open(template)
    page = testdoc[0]
    totalcards = 1
    
    # test if everything can fit in first card
    rect = descriptionrect_a 
    testtext = spell['text'][0]
    rc = page.insert_textbox(rect, testtext, fontsize = 7, # choose fontsize (float)
                       fontname = "Helvetica",         # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.85,
                       align = 0)                      # 0 = left, 1 = center, 2 = right

    if rc > 1:
        return
    
    # split text for first card
    totalcards = 2
    subtext1 = spell['text'][0].split(' ')
    subtext2 = list()
    rect = descriptionrect_a 
    
    count=0
    while count < 4:
       subtext2.insert(0,subtext1.pop())
       testtext = ' '.join(subtext1).lstrip()
       rc = page.insert_textbox(rect, testtext, fontsize = 7, # choose fontsize (float)
                          fontname = "Helvetica",       # a PDF standard font
                          fontfile = None,                # could be a file on your system
                          color=[1,1,1],
                          lineheight=0.85,
                          align = 0)  # 0 = left, 1 = center, 2 = right
       if rc > 1:
           count = count+1
       
    # test if everything can fit in second card
    rect = fitz.Rect(12, 17, 168, 230)   
    testtext = ' '.join(subtext2).lstrip()
    rc = page.insert_textbox(rect, testtext, fontsize = 7, # choose fontsize (float)
                       fontname = "Helvetica",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.85,
                       align = 0)                      # 0 = left, 1 = center, 2 = right
    
    # if two cards are sufficient, finalize
    if rc > 1:
        spell['text'] = [' '.join(subtext1).lstrip() + ' (1/2)',
                         ' '.join(subtext2).lstrip() + ' (2/2)']
        return  
    
    # 3rd card needed, condition for 3rd card
    totalcards = 3
    subtext3 = list()  
    count=0
    rect = fitz.Rect(12, 17, 168, 230)   
    while count < 4:
       subtext3.insert(0,subtext2.pop())
       testtext = ' '.join(subtext2).lstrip()
       rc = page.insert_textbox(rect, testtext, fontsize = 7, # choose fontsize (float)
                          fontname = "Helvetica",       # a PDF standard font
                          fontfile = None,                # could be a file on your system
                          color=[1,1,1],
                          lineheight=0.85,
                          align = 0)                      # 0 = left, 1 = center, 2 = right
       if rc > 1:
           count = count+1 
    
    
    # finalize
    spell['text'] = [' '.join(subtext1).lstrip() + ' (1/3)',
                     ' '.join(subtext2).lstrip() + ' (2/3)',
                     ' '.join(subtext3).lstrip() + ' (3/3)']
    


#####################################
## Read spell-list (xml) and add
## spells to the dictionary (list of spells)
##
## Input:   xml file
## Process: read spells, add entries in dict
## Output:  append spells to dictionary
#####################################
def read_spells(dictionary,spell_xml):
   with open(spell_xml, 'r') as f:
        data = f.read()    
        for each in BeautifulSoup(data, "xml").find_all('spell'):
          dictionary.append({
              'name':each.find('name').text,
              'classes':[x.strip() for x in each.find('classes').text.split(',')],
              'level':each.find('level').text,
              'school': each.find('school').text,
              'ritual': each.find('ritual').text,
              'time': each.find('time').text,
              'range': each.find('range').text,
              'components': each.find('components').text.partition(" (")[0],
              'duration': each.find('duration').text
                              .replace('minutes','min'),
              'text': [each.find('text').text.partition("Source: ")[0]
                           .replace("â€¢ ","#")
                           .replace('\\n','\r\n')
                           .replace('â€”','-')
                           .replace('âˆ’','-')]
              }) 
   return


#####################################
## generate single-sided card pdf with spell-image
##
## Input:   single spell from spell-dictionary;
##          output folder
## Process: copy _template.pdf;
##          write text on pdf, attributes and spell['text'][0];
##          search spell image, use spell['name'].png or else 0.png
## Output:  card pdf with name spell['name'].pdf
#####################################
def generate_maincard(spell,outputfolder):
    doc = fitz.open(template)
    page = doc[0] 
    
    #####################################
    # add FITZ Image Background
    #####################################
    page = doc[0]
    rect = fitz.Rect(10.3, 19.4, 168.2, 104.2)     
    text = spell['name']
    #page.draw_rect(rect)
    image="img/0.png"
    for root, dirs, files in os.walk(dir_path+"\img"):
        for file in files:
            if file.lower() == spell['name'].replace('/','').lower()+".png":
               image='img/'+file
    if image=="img/0.png":
       print("Warn: No image found for" + str(spell['text']))
    img = open(image, "rb").read()
    page.insert_image(rect, stream=img, keep_proportion=False)
  
    #####################################
    # add FITZ Title
    #####################################
    page = doc[0]
    rect = titlerect     
    text = spell['name']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 9, # choose fontsize (float)
                       fontname = "Times-BoldItalic",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[0,0,0],
                       lineheight=0.9,
                       align = 0)                      # 0 = left, 1 = center, 2 = right
    
    
  

    #####################################
    # add FITZ subtitle
    #####################################
    page = doc[0]
    rect = subtitlerect   
    text = ""
    if spell['level'] == '0':
        text = text + ('Cantrip ')
    else:    
        if      spell['level'] == '1':
            text = text + '1st level '
        elif spell['level'] == '2':
            text = text + '2nd level '
        elif spell['level'] == '3':
            text = text + '3rd level '
        elif spell['level'] == '4':
            text = text + '4th level '
        else:    
            text = text + spell['level'] + 'th level '
        
        if      spell['ritual'] == 'NO':
            text = text + 'spell '
        else:
            text = text + 'ritual '
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 9, # choose fontsize (float)
                       fontname = "Times-BoldItalic",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[0,0,0],
                       lineheight=0.9,
                       align = 0)                      # 0 = left, 1 = center, 2 = right
        
    #####################################
    # add FITZ School
    #####################################
    page = doc[0]
    rect = fitz.Rect(10, 105.3, 170, 120)    
    text = '('+spell['school']+')'
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 9, # choose fontsize (float)
                       fontname = "Times-BoldItalic",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[0,0,0],
                       lineheight=0.9,
                       align = 2)                      # 0 = left, 1 = center, 2 = right  
    
    
    #####################################
    # add FITZ Action Time
    #####################################
    x1=12
    y1=21
    
    page = doc[0]
    rect = fitz.Rect(x1, y1, x1+55, y1+13+16) 
    page.draw_rect(rect,fill=[0,0,0],stroke_opacity=0,fill_opacity=0.5)
    rect = fitz.Rect(x1, y1, x1+55, y1+13)     
    text = 'Casting Time'#spell['name']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 8, # choose fontsize (float)
                       fontname = "Helvetica-Bold",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.9,
                       align = 1)                      # 0 = left, 1 = center, 2 = right   
    rect = fitz.Rect(x1, y1+8, x1+55, y1+13+16)     
    text = spell['time']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 8, # choose fontsize (float)
                       fontname = "Helvetica",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.9,
                       align = 1)                      # 0 = left, 1 = center, 2 = right   
    
    #####################################
    # add FITZ Range
    #####################################
    x1=12
    y1=74
    
    page = doc[0]
    rect = fitz.Rect(x1, y1, x1+55, y1+13+16) 
    page.draw_rect(rect,fill=[0,0,0],stroke_opacity=0,fill_opacity=0.5)
    rect = fitz.Rect(x1, y1, x1+55, y1+13)     
    text = 'Range'#spell['name']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 8, # choose fontsize (float)
                       fontname = "Helvetica-Bold",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.9,
                       align = 1)                      # 0 = left, 1 = center, 2 = right   
    rect = fitz.Rect(x1, y1+8, x1+55, y1+13+16)     
    text = spell['range']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 8, # choose fontsize (float)
                       fontname = "Helvetica",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.9,
                       align = 1)                      # 0 = left, 1 = center, 2 = right      

    #####################################
    # add FITZ Components
    #####################################
    x1=113
    y1=21
    
    page = doc[0]
    rect = fitz.Rect(x1, y1, x1+55, y1+13+16) 
    page.draw_rect(rect,fill=[0,0,0],stroke_opacity=0,fill_opacity=0.5)
    rect = fitz.Rect(x1, y1, x1+55, y1+13)     
    text = 'Components'#spell['name']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 8, # choose fontsize (float)
                       fontname = "Helvetica-Bold",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.9,
                       align = 1)                      # 0 = left, 1 = center, 2 = right   
    rect = fitz.Rect(x1, y1+8, x1+55, y1+13+16)     
    text = spell['components']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 8, # choose fontsize (float)
                       fontname = "Helvetica",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.9,
                       align = 1)                      # 0 = left, 1 = center, 2 = right 

    #####################################
    # add FITZ Components
    #####################################
    x1=113
    y1=74
    
    page = doc[0]
    rect = fitz.Rect(x1, y1, x1+55, y1+13+16) 
    page.draw_rect(rect,fill=[0,0,0],stroke_opacity=0,fill_opacity=0.5)
    rect = fitz.Rect(x1, y1, x1+55, y1+13)     
    text = 'Duration'#spell['name']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 8, # choose fontsize (float)
                       fontname = "Helvetica-Bold",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.9,
                       align = 1)                      # 0 = left, 1 = center, 2 = right   
    rect = fitz.Rect(x1, y1+8, x1+55, y1+13+16)     
    text = spell['duration']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 8, # choose fontsize (float)
                      fontname = "Helvetica",       # a PDF standard font
                      fontfile = None,                # could be a file on your system
                      color=[1,1,1],
                      lineheight=0.9,
                      align = 1)                      # 0 = left, 1 = center, 2 = right 
    
    #####################################
    # add FITZ Text Description
    #####################################
    page = doc[0]
    rect = descriptionrect_a   
    
    
    # split text
    text = spell['text'][0]
    rc = page.insert_textbox(rect, text, fontsize = 7, # choose fontsize (float)
                       fontname = "Helvetica",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.835,
                       align = 0)                      # 0 = left, 1 = center, 2 = right

    if rc < 0:
       print('')
       print("FIRST SPELL TEXT TOO LONG")
       print(spell['name'])
       print(text)
       print(rc)
    

    #####################################
    # add FITZ Image Square
    #####################################
    page = doc[0]
    rect = fitz.Rect(151, 2, 151+24, 2+24)     
    text = spell['name']
    #page.draw_rect(rect)
    img = open("square.png", "rb").read()
    page.insert_image(rect, stream=img)
    
    #####################################
    # add FITZ level marker
    #####################################
    page = doc[0]
    rect = fitz.Rect(151.5, 3.8, 151.5+23, 3.8+23)     
    text = spell['level']
    #page.draw_rect(rect)
    img = open("square.png", "rb").read()
    page.insert_textbox(rect, text, fontsize = 14, # choose fontsize (float)
                       fontname = "Helvetica-Bold",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.9,
                       align = 1)                      # 0 = left, 1 = center, 2 = right  
    
    #####################################
    # Write PDF
    #####################################
    output_pdf_path = outputfolder+spell['name'].replace("/","")+'.pdf'
    doc.save(output_pdf_path)

#####################################
## generate single-sided card pdf without spell-image, for long ['text']
##
## Input:   single spell from spell-dictionary;
##          specify textindex of ['text'][index];
##          output folder where to write the pdf
##          
## Process: copy _template_extra.pdf;
##          write text on pdf, attributes and spell['text'][textindex];
## Output:  card pdf in fodler /out with name spell['name']+subindex.pdf
#####################################
def generate_subcard(spell,textindex,outputfolder,subindex):
    doc = fitz.open(template_extra)
    page = doc[0]
    
    #####################################
    # add FITZ Title
    #####################################
    page = doc[0]
    rect = titlerect     
    text = spell['name']
    #page.draw_rect(rect)
    page.insert_textbox(rect, text, fontsize = 9, # choose fontsize (float)
                       fontname = "Times-BoldItalic",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[0,0,0],
                       lineheight=0.9,
                       align = 0)                      # 0 = left, 1 = center, 2 = right    
    #####################################
    # add FITZ Text Description
    #####################################
    rect = descriptionrect_b 
    #page.draw_rect(rect)  
    text = spell['text'][textindex]
    
    # test if posible
    rc = page.insert_textbox(rect, text, fontsize = 7, # choose fontsize (float)
                       fontname = "Helvetica",       # a PDF standard font
                       fontfile = None,                # could be a file on your system
                       color=[1,1,1],
                       lineheight=0.835,
                       align = 0)                      # 0 = left, 1 = center, 2 = right

    if rc < 0:
       print("SUB SPELL TEXT IS TOO LONG")
       print(spell['name'])
       print(rc)    
    
    output_pdf_path = outputfolder+ spell['name'].replace("/","")+subindex+'.pdf'
    doc.save(output_pdf_path)    


def generate_pdf(spell,outputfolder):
    generate_maincard(spell,outputfolder)
    if len(spell['text']) > 1:
        generate_subcard(spell,1,outputfolder,'_b_')
    if len(spell['text']) > 2:
        generate_subcard(spell,2,outputfolder,'_c_')
    
    
  

# read in spells from XML files
print('### Reading spells from xml files')
spells = list()
for spell_source in sources:
    read_spells(spells,spell_source)
for spell in spells:
    condition_text(spell) 


print('### Filter for classes')
# filter unused
spells = [spell for spell in spells 
          if ('Cleric' in spell['classes']) 
          or ('Cleric (Knowledge)' in spell['classes'])]

print('### Generate individual spellcard PDF files')
# generate pdfs
for spell in spells:
    generate_pdf(spell,dir_path+'\\out\\')





#####################################
## Help functions to generate the printable PDF with 9 cards per double-sided A4 page
## function pdftoimg converta a pdf to a pixmap
## function placebackground places a background image behind the 9 cards (to fill distance between cards)
## function placecard places a single-sided card pdf at position 1-9 on the A4 page
#####################################
docwidth=595      # A4
docheight=842     
cardwidth=178.7   # standard spell card size
cardheigth=249.5
distance=10       # distance between spell cards

def pdftoimg(pdf,pg):
    doc = fitz.open(pdf)  # open document
    page = doc[pg]
    return page.get_pixmap(dpi=400).tobytes(output='png', jpg_quality=95)  # render page to an image

def placebackground(page,bgpixmap):
    x1 = (docwidth-3*cardwidth-3*distance)/2
    x2 = docwidth - x1
    y1 = (docheight-3*cardheigth-3*distance)/2
    y2 = docheight - y1
    rect = fitz.Rect(x1, y1, x2, y2)
    page.insert_image(rect, stream=bgpixmap, keep_proportion=False)
    return
    
# pos 1..9    
def placecard(page,cardpixmap,pos):
    row = pos // 3 # 0..0..0..1..1..
    col = pos % 3  # 0..1..2..
    x1 = (docwidth-3*cardwidth-3*distance)/2 + col*(cardwidth+distance) + distance/2
    y1 = (docheight-3*cardheigth-3*distance)/2 + row*(cardheigth+distance) + distance/2
    x2 = x1 + cardwidth
    y2 = y1 + cardheigth
    rect = fitz.Rect(x1, y1, x2, y2)
    page.insert_image(rect, stream=cardpixmap, keep_proportion=False)
    return    

##
## Spell texts have been split over 1-3 cards:
##      spell['text'] = ['text_a']
##      spell['text'] = ['text_a','text_b']
##      spell['text'] = ['text_a','text_b','text_c']
##
## Spells, therefore, have 1-3 single-sided PDF files.
## This function assigns the card PDF files to two-sided card PDF files. 
##      card[index] = ['front-pdf-link','back-pdf-link']
##
##      single sided output: card[index] = ['text_a_pdf','background']
##
##      double sided output: card[index] = ['text_a_pdf','text_b_pdf']
##
##      tripple sided output: card[index  ] = ['text_a_pdf','text_b_pdf'],
##                            card[index+1] = ['text_c_pdf','background']
##
## If a spell has 1 or 3 single-sided cards with text, then _background.pdf is used as background
##
print('### Generate print PDF files')
mydict = list()
for spell in spells:
    frontpdf = dir_path+'\\out\\'+spell['name'].replace("/","")+'.pdf'
    backpdf = dir_path+'\\_back.pdf'    
    if len(spell['text']) > 1:
        backpdf = dir_path+'\\out\\'+spell['name'].replace("/","")+'_b_.pdf'    
    mydict.append({
        'front': frontpdf,
        'back': backpdf
        })
    backpdf = dir_path+'\\_back.pdf' 
    if len(spell['text']) > 2:
        mydict.append({
            'front': dir_path+'\\out\\'+spell['name'].replace("/","")+'_c_.pdf',
            'back': backpdf
            })        


##
## Generate printable A4 pages with 9 double-sided cards per page
## and write the result in folder /print
##

# Initialize first two pages
cardcount = 0
pagecount = 0
bgimage=pdftoimg('_background.pdf',0)
printdoc = fitz.open()

currentpage_a = 0
printdoc.new_page(currentpage_a,width = docwidth,height = docheight)
placebackground(printdoc[currentpage_a],bgimage)

currentpage_b = 1
printdoc.new_page(currentpage_b,width = docwidth,height = docheight)
placebackground(printdoc[currentpage_b],bgimage)

for card in mydict:
    print("I am here, page " + str(pagecount) + " and card " + str(cardcount))
    if cardcount == 9:
       cardcount = 0
       pagecount = pagecount + 1
       
       currentpage_a = pagecount*2
       printdoc.new_page(currentpage_a,width = docwidth,height = docheight)
       placebackground(printdoc[currentpage_a],bgimage)
       
       currentpage_b = pagecount*2+1
       printdoc.new_page(currentpage_b,width = docwidth,height = docheight)
       placebackground(printdoc[currentpage_b],bgimage)
       
    placecard(printdoc[currentpage_a],pdftoimg(card['front'],0),cardcount)
    placecard(printdoc[currentpage_b],pdftoimg(card['back'],0),(2-cardcount%3)+3*(cardcount//3))
    cardcount = cardcount + 1

output_pdf_path = dir_path + '\\print\\' + 'output.pdf'
printdoc.save(output_pdf_path) # save the document





