import re, sys, requests
from flask import Flask
from flask import request
from flask import render_template
from flask import Markup
from nltk.tokenize import sent_tokenize,word_tokenize
from nltk.corpus import stopwords
from heapq import nlargest
from collections import defaultdict
from string import punctuation
from bs4 import BeautifulSoup


reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)


# Essentially, summarize() calls getWeight()
class Summ:
  def __init__(self, min_conf = 0.100, max_conf = 0.800):
    self._min_conf = min_conf
    self._max_conf = max_conf
    self._stopwords = set(stopwords.words('english') + list(punctuation))

  def getWeight(self, sentences):
    # Here we create a defaultdict object
    weight = defaultdict(int)
    # iterate through each sentence
    for s in sentences:
      for word in s: #for each word in the sentence, if it isn't a stop word, add 1 to the weight
        if word not in self._stopwords:
          weight[word] += 1
    # Return the largest weight and set it to m as a float
    maxVal = float(max(weight.values()))

    for w in weight.keys():
      # Set all weights to the same as before but this normalized by dividing by the max
      weight[w] /= maxVal
      # if the weight is greater than our max confidence we throw it out, it's probably something like common and irrelevant
      # if it is less than our min confidence it isn't common enough to be important to us
      if weight[w] >= self._max_conf or weight[w] <= self._min_conf:
        del weight[w]
    return weight # Return our dictionary after removing any unneeded words

  # Self refers to python class (this), text is the article text, numSentences is the number of sentences
  def summarize(self, text, numSentences):
    # Break the text into sentences
    sentenceList = sent_tokenize(text)
    # Check that the length of the list is more than the minimum sentences
    if(numSentences <= len(sentenceList)):
      sentences = [word_tokenize(s) for s in sentenceList] #turn our sentences into a list of words

      self._weight = self.getWeight(sentences)
      # rank dictionary to store the sentences and their weights
      rank = defaultdict(int)

      for count, sentenceTemp in enumerate(sentences):
        for word in sentenceTemp:
          if word in self._weight: # Check if word is one of the proper weighted words, if it is then up the sentences rank
            rank[count] += self._weight[word]

      # Return the top 3 sentences in the dictionary
      topSentences = nlargest(numSentences, rank, rank.get)

      return [sentenceList[j] for j in topSentences]

    else:
      print ("\nArticle too short to summarize! It must be atleast 3 sentences long!\n")
      sys.exit()


# calls summarize()
def getText(url):
 response = requests.get(url)
 try:
    if response.ok:
      html = response.content
      soup = BeautifulSoup(html, 'html')
 except NameError:
  print "No URL entered"
  sys.exit()
 # Join all the content in <p> tags by ' ' to form one big ol unicode obj
 text = '  '.join(map(lambda p: p.text, soup.find_all('p')))

 return soup.title.text, text

def getTitle(url):
 response = requests.get(url)
 try:
    if response.ok:
      html = response.content
      soup = BeautifulSoup(html, 'html')
 except NameError:
  print "No URL entered"
  sys.exit()
 # Join all the content in <p> tags by ' ' to form one big ol unicode obj
 text = '  '.join(map(lambda p: p.text, soup.find_all('p')))

 return soup.title.text

#***************************************************************************************************
# Pick any article url really
#***************************************************************************************************
def goURL(url):
  # instance of class
  Su = Summ()

  title, text = getText(url)

  count = 0
  tempStr = ""
  for sentence in Su.summarize(text, 3):
    count += 1
    sentence = re.sub('\n', "", sentence)
    tempStr += ("\n\n " + sentence.encode('utf-8'))
  return tempStr

@app.route('/')
def index_form():
  return render_template("indexFlask.html")

@app.route('/', methods =['POST'])
def index_form_post():
  text = request.form['UserUrl']
  return render_template('indexFlask.html', summ = goURL(text), title = getTitle(text))


if __name__ == 'main':
app.run(host='0.0.0.0', port=80)
