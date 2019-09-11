import io,sys
import xml.etree.ElementTree as ET

class UkeTab:

    def convertToText(self,infile,outfile):
        """ Convert a musescore uke tab into text.
            infile = source file (.mscx)
            outfile = dest text. "-" = stdout"""
        if (infile is None or outfile is None):
            self.printhelp()
            return
        tree=ET.parse(infile)
        if (outfile=="-"):
            dest=sys.stdout
        else:
            dest=open(outfile,"w")
        try:
            self.process(tree,dest)
        finally:
            if not(outfile is sys.stdout):
                dest.close()

    def process(self,tree,dest):
        """ Process mscx to text """
        root=tree.getroot()
        self.dest = dest
        if root.tag!="museScore":
            self.adderr("Not a musescore file.")
            return
        self.addln("Testing output: ",root,root.tag)
        for staff in root.findall(".//Score/Staff"):
            self.processStaff(staff)

    def processStaff(self,staff):
        """ Process staff Element """
        self.addln(staff)
        self.output_staff=["","","",""]
        self.output_lyrics=""
        for measure in staff.findall("./Measure"):
            mystaff=["|","|","|","|"]
            lyrics=""
            for voice in measure.findall("voice"):
                for child in voice:
                    if child.tag=="Chord" or child.tag=="Rest":
                        chord=child
                        duration=self.getvalue(chord,"durationType")
                        space=self.fillnote("",duration)
                        mychord=[space,space,space,space]
                        if chord.tag=="Chord":
                            for note in chord.findall("./Note"):
                                astring=self.getvalue(note,"string")
                                afret=self.getvalue(note,"fret")
                                snum=int(astring)
                                mychord[snum]=self.fillnote(afret,duration)
                        chord_lyric=self.getvalue(chord,"Lyrics/text")
                        if not(chord_lyric is None):
                            syllabic=self.getvalue(chord,"Lyrics/syllabic")
                            sep = "-" if (syllabic=="begin" or syllabic=="middle") else " "
                            lyrics=self.addLyric(mystaff,lyrics,chord_lyric,sep)
                        for i in range(len(mychord)):
                            mystaff[i]+=mychord[i]
                        self.fixLength(mystaff,lyrics)
                                                
            if len(mystaff[0])+len(self.output_staff[0])>=110: self.dumpstaff()
            self.addMeasure(mystaff,lyrics)
            
        self.dumpstaff()

    def dumpstaff(self):
        strings = ['A','E','C','G']
        for i in range(len(self.output_staff)):
            self.addln(strings[i]+self.output_staff[i]+"|")
            self.output_staff[i]=""
        if len(self.output_lyrics)>0:
            self.addln(" "+self.output_lyrics)
            self.output_lyrics=""
        self.addln()
                       
    def fillnote(self,value,duration):
        ln=2
        if duration=="quarter": ln=4
        result=value
        while len(result)<ln: result+="-"
        return result

    def addLyric(self,mystaff,lyrics,lyric,sep):
        while len(lyrics)<len(mystaff[0]): lyrics+=" "
        lyrics+=lyric.strip()+sep
        return lyrics

    def addMeasure(self,mystaff,lyrics):
        if (lyrics!=""):
            while len(self.output_lyrics)<len(self.output_staff[0]):
                       self.output_lyrics+=" "
        for i in range(len(mystaff)):
            self.output_staff[i]+=mystaff[i]
        self.output_lyrics+=lyrics
        
    def fixLength(self,mystaff,lyrics):
        while len(mystaff[0])<len(lyrics):
            for i in range(len(mystaff)):
                mystaff[i]+="-"
                
    def getvalue(self,node,tag):
        """ Return the text value of a child element, or None if not found """
        child=node.find(tag)
        if child is None: return None
        return child.text
    
    def addln(self,*msg):
        """ Output line to destination file. """
        print(*msg,file=self.dest)

    def adderr(self,*msg):
        print(*msg,file=sys.stderr)
            

    def printHelp(self):
        """ Print basic usage """
        print("Usage: python -m uketab infile outfile")
        return


if __name__=="__main__":
    uk=UkeTab()
    src=r"C:\Users\robbi\OneDrive\Documents\MuseScore3\Scores\major.mscx"
    uk.convertToText(src,"-")
        
    
