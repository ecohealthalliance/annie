import csv
import codecs
"""Read Draper CSV files"""

class DraperReader:

    def __init__(self, filename='tests/annotator/resources/Train_TreatmentCapacityShortage.csv'):

        lines = self.lines(filename)
        self.reader = csv.reader(lines)

    # csvreader isn't unicode aware? sheesh. have to read into unicode, covert
    # to utf8 for csvreader, then pump back out as unicode.
    def lines(self, filename):
        lines = codecs.open(filename, 'r', 'utf8')
        for line in lines:
            yield line.encode('utf8')

    def articles(self):

        header = self.reader.next()

        for row in self.reader:
            yield { 'id': row[0],
                    'text': row[5].decode('utf8'),
                    'label': row[8] }

