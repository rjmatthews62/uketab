import io,sys
import xml.etree.ElementTree as ET
import argparse

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
        self.tree=tree
        root=tree.getroot()
        self.root=root
        self.dest = dest
        if root.tag!="museScore":
            self.adderr("Not a musescore file.")
            return
        self.addln("Testing output: ",root,root.tag)
        for staff in root.findall(".//Score/Staff"):
            if self.output_type=="chords":
                self.chordsLyrics(staff)
            else:
                self.processStaff(staff)

    def processStaff(self,staff):
        """ Process staff Element """
        self.addln(staff)
        self.output_staff=["","","",""]
        self.getminlength(staff)
        self.output_lyrics=""
        measurelist=staff.findall("./Measure")
        m=0
        startrepeat=0
        loop=0
        while m<len(measurelist):
            measure=measurelist[m]
            m+=1
            if measure.find("startRepeat")!=None:
                startrepeat=m-1
        #for measure in staff.findall("./Measure"):
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
                                if not(self.isTie(note)):
                                    mychord[snum]=self.fillnote(afret,duration)
                        lyric_search="Lyrics"
                        if loop>0:
                            lyric_search="Lyrics[no='%d']" % loop
                        chord_lyric=self.getvalue(chord,lyric_search+"/text")
                        if not(chord_lyric is None):
                            syllabic=self.getvalue(chord,lyric_search+"/syllabic")
                            sep = "-" if (syllabic=="begin" or syllabic=="middle") else " "
                            lyrics=self.addLyric(mystaff,lyrics,chord_lyric,sep)
                        for i in range(len(mychord)):
                            mystaff[i]+=mychord[i]
                        self.fixLength(mystaff,lyrics)
                                                
            if len(mystaff[0])+len(self.output_staff[0])>=110: self.dumpstaff()
            self.addMeasure(mystaff,lyrics)
            rpt=measure.find("endRepeat")
            if not(rpt is None):
                rptcount=int(rpt.text)
                if (loop<rptcount-1):
                    loop+=1
                    m=startrepeat
                else:
                    loop=0
        self.dumpstaff()

    def chordsLyrics(self,staff):
        self.addln("Staff: "+self.getStaffName(staff))
        self.output_lyrics=""
        chords=""
        lyrics=""
        for measure in staff.findall("./Measure"):
            for voice in measure.findall("voice"):
                for child in voice:
                    if child.tag=="Chord" or child.tag=="Rest":
                        chord=child
                        chord_lyric=self.getvalue(chord,"Lyrics/text")
                        
                        if not(chord_lyric is None):
                            syllabic=self.getvalue(chord,"Lyrics/syllabic")
                            sep = "" if (syllabic=="begin" or syllabic=="middle") else " "
                            lyrics+=chord_lyric+sep
                        lyrics=self.matchlen(lyrics,chords)
                        
                    elif child.tag=="Harmony":
                        chordname=self.getChordName(child)
                        chords=self.matchlen(chords,lyrics)
                        if not(chords=="" or chords.endswith(" ")):
                            chords+=" "
                        chords+=chordname
                if len(lyrics)>80:
                    self.addln(chords)
                    self.addln(lyrics)
                    lyrics=""
                    chords=""
        self.addln(chords)
        self.addln(lyrics)
        

    def getStaffName(self,staff):
        id=staff.attrib['id']
        #track=self.root.find('./Score/Part[Staff[@id="'+id+'"]]/trackName')
        track=self.root.find('./Score/Part/Staff[@id="'+id+'"]/../trackName')
        name=id+" "+track.text if not(track is None) else str(id)
        return name

    def getChordName(self,harmony):
        croot=self.getvalue(harmony,"root")
        cname=self.getvalue(harmony,"name")
        if cname is None: cname=""
        if croot is None:
            return ""
        else:
            chordnames={8:"Gb",9:"Db",10:"Ab",11:"Eb",12:"Bb",13:"F",14:"C",15:"G",16:"D",17:"A",18:"E",19:"B",20:"F#",21:"C#",22:"G#"}
            nroot=int(croot)
            if nroot in chordnames:
                croot=chordnames[nroot]
        return croot+cname
    
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
        ln=max((self.calclength(duration)-self.minlen)+1,1)
        result=value
        while len(result)<ln: result+="-"
        return result

    def matchlen(self,target,source):
        while len(target)<len(source): target+=" "
        return target
    
    def isTie(self,note):
        nd=note.find("Spanner[@type='Tie']/prev")
        return not(nd is None)
    
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

    def getminlength(self,staff):
        self.minlen=self.calclength('whole')
        for duration in staff.findall(".//durationType"):
            self.minlen=min(self.minlen,self.calclength(duration.text))

    def calclength(self,duration):
        ix=0
        if duration=="measure":
            duration="whole"
        try:
            ix=['16th','eighth','quarter','half','whole'].index(duration)
        except ValueError:
            ix=2
        return ix
    
    def addln(self,*msg):
        """ Output line to destination file. """
        print(*msg,file=self.dest)

    def adderr(self,*msg):
        print(*msg,file=sys.stderr)
            

    def printHelp(self):
        """ Print basic usage """
        print("Usage: python -m uketab infile outfile")
        return

    def parseArguments(self,arglist=None):
        parser=argparse.ArgumentParser(description="Ukulele tab exporter")
        parser.add_argument('--option',choices=['tab','chords'],default='tab')
        parser.add_argument('source')
        parser.add_argument('dest',nargs='?',default='-')
        result=parser.parse_args(arglist)
        self.output_type=result.option
        print(self.output_type)
        print("From=",result.source," Dest",result.dest)
        self.convertToText(result.source,result.dest)
        


if __name__=="__main__":
    uk=UkeTab()
    #src=r"C:\Users\robbi\Dropbox\Public\Scores\Under_Your_Spell_Standing_Reprise.mscx"
    #dest="-"
    uk.parseArguments()
    #uk.output_type="chords"
    #uk.convertToText(src,"-")
        
    
