from bokeh.charts import Dot, show, output_file
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import fpdf, requests
import csv

from pytagcloud import create_tag_image, make_tags
from pytagcloud.lang.counter import get_tag_counts

def wordCloud(pname, ftype, text):
    if (ftype=="keywords"):
        tags = make_tags(get_tag_counts(text), maxsize=25)
    else:
        tags = make_tags(get_tag_counts(text), maxsize=120)
    create_tag_image(tags, pname+'_'+ftype+'_word_cloud.png', size=(900, 600), fontname='Lobster')

def dotplot(pname, filename, data, title, ylabel):
    titlex=pname+" : "+title
    filename=filename+"_"+title
    output_file(filename+".html")
    values = [value for name, value in data.items()]
    names = [name for name, value in data.items()]
    dots = Dot(values, cat=names, title=titlex, ylabel=ylabel, legend=False)
    show(dots)

def entityNetwork(pname, filename, relatedEntities):
    G=nx.Graph()
    for name,value in relatedEntities.items():
        G.add_edge(pname, value)
    pos=nx.spring_layout(G)
    if (len(relatedEntities)>0):
        colors=range(G.number_of_edges())
    else:
        colors=range(1)
    nx.draw(G,pos,node_color='#A0CBE2',edge_color=colors,width=4,with_labels=True)
    plt.savefig(filename+"_entities.png")
    
def barplot(pname, traits):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    ind = np.arange(1,len(traits)+1)      # the x locations for the groups
    width = 0.2                           # the width of the bars
    values = [int(float(value)*100) for name, value in traits.items()]
    rects1 = ax.bar(ind, values, width,color=['blue','red','green','black','orange','yellow','purple'])
    ax.set_xlim(0,len(ind)+2)
    ax.set_ylim(0,100)
    ax.set_ylabel('Scores')
    ax.set_title('Traits')
    legends = [name for name,value in traits.items()]
    ax.legend( rects1, legends )
    
    plt.savefig(pname+".png", bbox_inches='tight')
    
def callFullContact(email):
    apiKey = '%%%'
    url="https://api.fullcontact.com/v2/person.json?email="+email+"&style=dictionary&apiKey="+apiKey
    resp=requests.get(url)

def writeToFile(name, piData, eeData, twitterFeedData):
    outFilename = name + ".out"
    outFile = open(outFilename,'w')
    outFile.write("persona report for " + name)
    outFile.write("\n")
    outFile.write("------------------------------------"+"\n")
    outFile.write("personality insights ")
    outFile.write("\n")
    for name,value in piData.items():
        outFile.write(name+" "+str(value)+"\n")
    outFile.write("------------------------------------"+"\n")
    outFile.write("related entities"+"\n")
    for name,value in eeData.items():
        outFile.write(name+" "+value+"\n")
    outFile.write("------------------------------------"+"\n")
    outFile.write("tweets"+"\n")
    outFile.write(twitterFeedData)
    outFile.close()

def createPDF(pname, piData, eeData, twitterFeedData, sentiment, spsScore):
    pdf = fpdf.FPDF(format='letter')
    pdf.add_page()
    pdf.set_font("Arial", style='BU', size=14)
    pdf.cell(200, 10, txt="Persona Report For "+pname, border=0,ln=1, align="C")
    spsScore="SPS:"+str(spsScore)
    pdf.cell(200, 10, txt=spsScore, border=0,ln=1, align="C")
    pdf.set_font("Arial", style='U', size=12)
    pdf.cell(200, 10, txt="Personality Traits",border=0,ln=1,align='C')
    pdf.image(pname+".png",w=100,h=50)
    #pdf.set_font("Arial", style='', size=9)
    #for name,value in piData.items():
    #    valueS = name+":"+"{0:.2f}".format(float(value))
    #    pdf.cell(200, 8, txt=valueS, border=1, ln=1, align='C')
    pdf.set_font("Arial", style='U', size=12)
    pdf.cell(200,10,txt="Top Related Entities",border=0,ln=1,align='C')
    pdf.set_font("Arial", style='', size=9)
    for name,value in eeData.items():
        valueS=name+":"+value
        pdf.cell(200, 8, txt=valueS, border=1, ln=1, align='C')
    pdf.set_font("Arial", style='U', size=12)
    pdf.cell(200,10,txt="Recent Tweets..",border=0,ln=1,align='C')
    pdf.set_font("Arial", style='', size=9)
    for i in range(len(twitterFeedData)):
        if (i<10):
            pdf.cell(200, 10, txt=twitterFeedData[i], border=0, ln=1, align='C')
        else:
            break
    pdf.set_font("Arial", style='U', size=12)
    pdf.cell(200,10,txt="Tweet Sentiment",border=0,ln=1,align='C')
    pdf.set_font("Arial", style='', size=9)
    sentimentOut = "type="+sentiment['type']+" score="+sentiment['score']
    pdf.cell(200,10,txt=sentimentOut,border=1,ln=1, align='C')
    pdf.output(pname+".pdf")
    
def spsScore(name):
    f = open("scores.txt", 'rt')
    try:
        persons = csv.reader(f)
        for person in persons:
            if (person[0].lower()==name):
                sentiment=person[1]
                sent_score=person[2]
                cps_score=person[3]
    finally:
        f.close()
    return sentiment,sent_score,cps_score