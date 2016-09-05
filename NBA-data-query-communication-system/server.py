#!/usr/bin/env python2.7

"""
To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os, time , datetime
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#Your database uri
DATABASEURI = ""


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


loginlist = []


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def mainpage():
  return render_template('mainpage.html')

@app.route('/dataquery')
def dataquery():
  return render_template('main_page.html')

@app.route('/index')
def index():

  name = request.args.get('name')
  if name == 'user':
    cursor = g.conn.execute("SELECT username, password FROM Account")
    user_info = {}
    for result in cursor:
      user_info[result['username']] = result['password']
     
  #print user_info  # can also be accessed using result[0]
    cursor.close()
  

  #
    dict = {'name': 'user' , 'info': user_info}  
#
    return render_template("index.html", dict = dict)
  else:
    cursor = g.conn.execute("SELECT username, password FROM administrator")
    admin_info = {}
    for result in cursor:
      admin_info[result['username']] = result['password']
     
  #print user_info  # can also be accessed using result[0]
    cursor.close()
  

  #
    dict = {'name': 'admin' , 'info': admin_info}
  #
    return render_template("index.html", dict = dict)
#

#The data mainpage
@app.route('/data')
def data():
  cursor = g.conn.execute("select * from player")
  player_dict = {}
  for result in cursor:
    player_dict[result['pname']] = result['pdata']
  #print player_dict
  cursor.close()
  #player = request.form['player']
  #print 'the input is %s' % player
  #if player in player_dict.keys():
  #  weburl = "/player/%s" % player
  #  return redirect(weburl)
 
  return render_template("data.html")


@app.route('/get_player', methods=['POST'])
def get_player():
  player = request.form['player']
  weburl = "/player/%s" % player
  return redirect(weburl)

@app.route('/get_team', methods=['POST'])
def get_team():
  team = request.form['team']
  weburl = "/team/%s" % team
  return redirect(weburl)

@app.route('/player/<player>')
def player(player):
  cursor = g.conn.execute("select * from player")
  player_dict = {}
  pict = {}
  video = {}
  for result in cursor:
    player_dict[result['pname']] = result['pdata']
    pict[result['pname']] = result['picture']
    video[result['pname']] = result['video']
    
  #print player_dict
  cursor.close()
  #print 'next step'
  cursor = g.conn.execute("select tname from player, belongs, team where player.pid = belongs.pid and belongs.tid = team.tid and player.pname='%s';" % player)
  for result in cursor:
    tname = result['tname']
  cursor.close()
  context = {}
  context['name'] = player
  context['score'] = player_dict[player][0]
  context['rebound'] = player_dict[player][1]
  context['assists'] = player_dict[player][2]
  context['picture'] = pict[player]
  context['video'] = video[player]
  context['tname'] = tname
  return render_template("player.html", **context)

@app.route('/team/<team>')
def team(team):
  cursor = g.conn.execute("select * from team")
  team_dict = {}
  logo_dict = {}
  for result in cursor:
    team_dict[result['tname']] = result['location']
    logo_dict[result['tname']] = result['logo']
    #print result['tname'], result['location']
  cursor.close()
  player = []
  cursor = g.conn.execute("select pname from player, belongs, team where player.pid = belongs.pid and team.tid = belongs.tid and tname = '%s';" % team)
  for result in cursor:
    player.append(result['pname'])
  #print player
  context = {}
  context['name'] = team
  context['location'] = team_dict[team]
  context['player'] = player
  context['logo'] = logo_dict[team]
  #print context
  return render_template("team.html", **context)

#These functions are for the game data
@app.route('/game')
def game():
  print 'In game function'
  return render_template('game.html')


@app.route('/get_game_date',methods=['POST'])
def get_game_date():
  date = request.form['date']
  #print date
  weburl = "/gamedate/%s" % date
  print weburl
  return redirect(weburl)

@app.route('/get_game_team',methods=['POST'])
def get_game_team():
  team = request.form['team']
  #print team
  weburl = 'gameteam/%s' % team
  return redirect(weburl)

@app.route('/gameteam/<team>')
def getteam(team):
  print team
  context = {}

  query = "select g.hostscore, g.guestscore, g.time, t2.tname as guestteam from game as g, team as t1, team as t2 where g.hostid = t1.tid and g.guestid = t2.tid and t1.tname = '%s';" % str(team)
  cursor = g.conn.execute(query)
  host_list = []
  for result in cursor:
    dict = {}
    dict['time'] = result['time']
    dict['guestteam'] = result['guestteam']
    dict['hostscore'] = result['hostscore']
    dict['guestscore'] = result['guestscore']
    host_list.append(dict)
  context['host'] = host_list
  cursor.close()
  print 'host query finished'

  query = "select g.hostscore, g.guestscore, g.time, t1.tname as hostteam from game as g, team as t1, team as t2 where g.hostid = t1.tid and g.guestid = t2.tid and t2.tname = '%s';" % str(team)
  cursor = g.conn.execute(query)
  guest_list = []
  for result in cursor:
    dict = {}
    dict['time'] = result['time']
    dict['hostteam'] = result['hostteam']
    dict['hostscore'] = result['hostscore']
    dict['guestscore'] = result['guestscore']
    guest_list.append(dict)
  context['guest'] = guest_list
  cursor.close()
  context['team'] = team
  print 'guest query finished'
  print context
  return render_template('gameteam.html', **context)
  
@app.route('/gamedate/<date>')
def gamedate(date):
  #print 'hello'
  #d = datetime.strptime(str(date), '%Y-%m-%d')
  #print d['date']
  #dd = datetime.strftime('%Y-%m-%d',struct_time(date))
  query = "select t1.tname as hostname, t2.tname as guestname, g.hostscore, g.guestscore from team as t1, team as t2, game as g where t1.tid = g.hostid and t2.tid = g.guestid and g.time = '%s'" % str(date)
  #print query
  game_dict = []
  cursor = g.conn.execute(query)
  for result in cursor:
    dict = {}
    dict['hostname'] = result['hostname']
    dict['time'] = date
    dict['hostscore'] = result['hostscore']
    dict['guestscore'] = result['guestscore']
    dict['guestname'] = result['guestname']
    game_dict.append(dict)
  cursor.close()
  context = {}
  context['game'] = game_dict
  return render_template('gamedate.html', **context)

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
  return redirect('/')

@app.route('/login', methods=['POST' , 'GET'])
def login():
  name = request.args.get('name')
  print name
  if name == 'user':
    cursor = g.conn.execute("SELECT username, password FROM Account")
  else:
     cursor = g.conn.execute("SELECT username, password FROM administrator")
  user_info = {}
  for result in cursor:
    user_info[result['username']] = result['password']
     
  #print user_info  # can also be accessed using result[0]
  cursor.close()


  username = request.form['username']
  #print username
  password = request.form['password']
  #print password
  #print user_info
  for i in user_info.keys():
    if i == str(username) and user_info[i] == str(password):
      print 'Welcome %s' % username
      
      weburl = "/" + name + "page" + "?username=" + username
      return redirect(weburl)
      #return render_template("main_page.html", **context)
  return redirect('/index?name=%s'%name)

@app.route('/register' , methods = ['GET' , 'POST'])
def register():
  return render_template('register.html')

@app.route('/userpage' , methods = ['GET' , 'POST'])
def user():
  username = request.args.get('username')
  if request.method == 'POST':
    newusername = request.form['username']
    newpassword = request.form['password']
    newemail = request.form['email']
    cursor = g.conn.execute("SELECT username FROM Account")
    for result in cursor:
      if newusername == result['username']:
        return redirect('/register')
    blockflag = 0
    count = 0
    cursor = g.conn.execute("SELECT COUNT(*) FROM account")
    for result in cursor:
      count = result['count']
    userid = count + 1
    g.conn.execute("INSERT INTO account VALUES ('{0}' , '{1}' , '{2}' , '{3}' , '{4}')".format(int(userid) , str(newusername) , str(newpassword) , str(newemail) , int(blockflag)))
    return redirect("/userpage?username=%s" % newusername)

  username = request.args.get('username')
  loginflag = 0
  """ 
  for item in loginlist:
    if username == item:
      loginflag = 1
  if loginflag == 1:
    dict = {'username': username}
    return render_template("already_login.html" , dict = dict)
  else:
    loginlist.append(username)"""
  cursor = g.conn.execute("SELECT * FROM Account")
  user_info = {}
  for result in cursor:
    #print result
    if result['username'] == username:
      user_info['userid'] = result['userid']
      user_info['username'] = result['username']
      user_info['password'] = result['password']
      user_info['email'] = result['email']
      block = str(result['blockflag'])
      if int(block) == 0:
        user_info['blockflag'] = "No"
      else:
        user_info['blockflag'] = "Yes"
  cursor = g.conn.execute("SELECT * FROM postssend WHERE uid = %d" %int(user_info['userid']))
  posts = []
  for result in cursor:
    posts.append({'content': result['content'] , 'time': result['posttime']})
  user_info['posts'] = posts  
  cursor.close();
  return render_template('user_homepage.html' , user_info = user_info)

@app.route('/account_setup' , methods = ['GET' , 'POST'])
def setup():
  username = str(request.args.get('username'))
  cursor = g.conn.execute("SELECT * FROM account WHERE username = '%s'" % username)
  for result in cursor:
    password = result['password']
    email = result['email']
  dict = {'username': username , 'password': password , 'email': email}
  return render_template("account_setup.html" , dict = dict)
  
@app.route('/setup' , methods = ['GET' , 'POST'])
def set():
  username = request.args.get('username')
  newpassword = request.form['password']
  print newpassword , username
  g.conn.execute("UPDATE account SET password = '{0}' WHERE username = '{1}'".format(str(newpassword) , str(username)))
  dict = {'username': str(username)}
  return render_template("setsuccess.html" , dict = dict);

@app.route('/logout')
def logout():
  username = request.args.get('username')
  #loginlist.remove(username)
  dict = {'name': 'user'}
  return render_template("logout.html" , dict = dict)

@app.route('/forum')
def forum():
  username = request.args.get('username')
  cursor = g.conn.execute("SELECT * FROM postssend")
  posts = []
  cursor = g.conn.execute("SELECT content , username , posttime FROM postssend AS p, account AS a WHERE a.userid = p.uid")
  for result in cursor:
    posts.append({'login_user': str(username) , 'user': result['username'] , 'content': result['content'] , 'time': result['posttime']})
  #print posts
  cursor = g.conn.execute("SELECT min(posttime) , max(posttime) FROM postssend")
  minposttime = ""
  maxposttime = ""
  for result in cursor:
    minposttime = str(result['min'])
    maxposttime = str(result['max'])
  dict = {'posts': posts , 'minposttime': minposttime , 'maxposttime': maxposttime}
  cursor.close()
  return render_template('forum.html' , dict = dict)

@app.route('/forum/filter' , methods = ['GET' , 'POST'])
def forumfilter():
  username = str(request.args.get('username'))
  content = '%%' + str(request.form['content']) + '%%'
  startdate = datetime.datetime.strptime(str(request.form['from']) + ' 00:00:00' , '%Y-%m-%d %H:%M:%S')
  enddate = datetime.datetime.strptime(str(request.form['to']) + ' 23:59:59' , '%Y-%m-%d %H:%M:%S')
  posts = []
  if content == "%%all%%":
    cursor = g.conn.execute("SELECT content , username , posttime FROM postssend AS p , account AS a WHERE a.userid = p.uid AND p.posttime >= '{1}' AND p.posttime <= '{2}'".format(content , startdate , enddate))
  else:
    cursor = g.conn.execute("SELECT content , username , posttime FROM postssend AS p , account AS a WHERE a.userid = p.uid AND p.content LIKE '{0}' AND p.posttime >= '{1}' AND p.posttime <= '{2}'".format(content , startdate , enddate))
  for result in cursor:
    posts.append({'login_user': str(username) , 'user': result['username'] , 'content': result['content'] , 'time': result['posttime']})
  cursor = g.conn.execute("SELECT min(posttime) , max(posttime) FROM postssend")
  minposttime = ""
  maxposttime = ""
  for result in cursor:
    minposttime = str(result['min'])
    maxposttime = str(result['max'])
  if len(posts) == 0:
    return render_template('empty.html' , dict = {'posts': [{'login_user': str(username) , 'section': 'post'}] , 'minposttime': minposttime , 'maxposttime': maxposttime})
  dict = {'posts': posts , 'minposttime': minposttime , 'maxposttime': maxposttime}
  #print dict
  cursor.close()
  return render_template('forum.html' , dict = dict)

@app.route('/send', methods=['POST'])
def send():
  if request.method == 'POST':
    ISOTIMEFORMAT='%Y-%m-%d %X'
    post = str(request.form.get('post'))
    poster = str(request.args.get('poster'))
    cursor = g.conn.execute("SELECT blockflag FROM account WHERE username = '%s'" % poster)
    ifblock = 0
    for result in cursor:
      ifblock = int(result['blockflag'])
    if ifblock == 1:
      dict = {'username': poster}
      return render_template("already_block.html" , dict = dict)
    if post.find('\'') != -1:
      post = post.replace('\'' , '\'\'')
    posttime = time.strftime( ISOTIMEFORMAT, time.localtime( time.time() ) )
    count = 0
    cursor = g.conn.execute("SELECT userid FROM account WHERE username = '%s'" % poster)
    for result in cursor:
      uid = result['userid']
    cursor = g.conn.execute("SELECT COUNT(*) FROM postssend")
    for result in cursor:
      count = result[count]
    while 1:
      try:
        #print "iteration"
        count += 1
        #print count
        pid = count
        g.conn.execute("INSERT INTO postssend VALUES ('{0}' ,'{1}', '{2}', '{3}')".format(int(pid), str(uid) , post , str(posttime)))
      except:
        #print "error"
        continue
      break
    cursor.close()
    return redirect("/forum?username=%s" %poster)

@app.route('/adindex' , methods = ['GET' , 'POST'])
def adindex():
  cursor = g.conn.execute("SELECT username, password FROM administrator")
  user_info = {}
  for result in cursor:
    user_info[result['username']] = result['password']

  #print user_info  # can also be accessed using result[0]
  cursor.close()


  #
  context = dict(data = user_info.keys())
  #
  return render_template("adindex.html", **context)

@app.route('/adlogin' , methods = ['GET' , 'POST'])
def adlogin():
  cursor = g.conn.execute("SELECT username, password FROM administrator")
  admin_info = {}
  for result in cursor:
    admin_info[result['username']] = result['password']

  #print user_info  # can also be accessed using result[0]
  cursor.close()


  username = request.form['username']
  #print username
  password = request.form['password']
  #print password
  #print user_info
  for i in admin_info.keys():
    if i == str(username) and admin_info[i] == str(password):
      print 'Welcome %s' % username

      weburl = '/adminpage?username=%s' % username
      return redirect(weburl)
      #return render_template("main_page.html", **context)
  return redirect('/adlogin')

@app.route('/adminpage' , methods = ['GET' , 'POST'])
def adminpage():
  username = request.args.get('username')
  if request.method == 'POST':
    newusername = request.form['adminname']
    newpassword = request.form['adminpassword']
    cursor = g.conn.execute("SELECT username FROM administrator")
    for result in cursor:
      if newusername == result['username']:
        return redirect('/register')
    count = 0
    cursor = g.conn.execute("SELECT COUNT(*) FROM administrator")
    for result in cursor:
      count = result['count']
    aid = count + 1
    g.conn.execute("INSERT INTO administrator VALUES ('{0}' , '{1}' , '{2}')".format(int(aid) , str(newusername) , str(newpassword)))
    return redirect("/adminpage?username=%s" % newusername)
  cursor = g.conn.execute("SELECT * FROM administrator")
  admin_info = {}
  for result in cursor:
    #print result
    if result['username'] == username:
      admin_info['aid'] = result['aid']
      admin_info['username'] = result['username']
      admin_info['password'] = result['password']
  cursor.close();
  return render_template('adminpage.html' , admin_info = admin_info)

@app.route('/userlist' , methods = ['GET' , 'POST'])
def userlist():
  username = request.args.get('username')
  cursor = g.conn.execute("SELECT * FROM Account")
  userlist = []
  user_info = {}
  for result in cursor:
    user_info = {}
    user_info['userid'] = result['userid']
    user_info['username'] = result['username']
    user_info['password'] = result['password']
    user_info['email'] = result['email']
    block = str(result['blockflag'])
    if int(block) == 0:
      user_info['blockflag'] = "No"
    else:
      user_info['blockflag'] = "Yes"
    userlist.append(user_info)
  for user in userlist:
    cursor = g.conn.execute("SELECT * FROM postssend WHERE uid = %d" %int(user['userid']))
    posts = []
    for result in cursor:
      posts.append({'content': result['content'] , 'time': result['posttime']})
    user['posts'] = posts
    cursor.close();
  dict = {'username': username , 'userlist': userlist}
  return render_template("userlist.html" , dict = dict)

@app.route("/usermanage" , methods = ['GET' , 'POST'])
def usermanage():
  username = request.args.get('username')
  adminname = request.args.get('adminname')
  cursor = g.conn.execute("SELECT blockflag FROM account WHERE username = '%s'" % str(username))
  for result in cursor:
    if int(result['blockflag']) == 1:
      g.conn.execute("UPDATE account SET blockflag = 0 WHERE username = '%s'" % str(username))
    else:
       g.conn.execute("UPDATE account SET blockflag = 1 WHERE username = '%s'" % str(username))
  return redirect('/userlist?username=%s'%adminname)

@app.route("/forummanage" , methods = ['GET' , 'POST'])
def forummanage():
  adminname = request.args.get("username")
  post = []
  cursor = g.conn.execute("SELECT a.username , p.content , p.posttime FROM account AS a , postssend AS p WHERE a.userid = p.uid")
  for result in cursor:
    dict = {'content': result['content'] , 'username': result['username'] , 'time': result['posttime']}
    post.append(dict)
  dict = {'adminname': adminname , 'post': post}
  return render_template('forummanage.html' , dict = dict)  
  
@app.route("/deletepost" , methods = ['GET' , 'POST'])
def deletepost():
  adminname = request.args.get('adminname')
  content = request.args.get('content')
  if content.find('\'') != -1:
    content = content.replace('\'' , '\'\'')
  g.conn.execute("DELETE FROM postssend WHERE content = '%s'" %str(content))
  return redirect("/forummanage?adminname=%s"%adminname)

@app.route("/modifypage" , methods = ['GET' , 'POST'])
def modifypage():
  adminname = request.args.get('username')
  return render_template('modifydata.html' , dict = {'username': str(adminname)})

@app.route("/modifydata" , methods = ['GET' , 'POST'])
def modifydata():
  adminname = request.args.get('username')
  date = request.form['date']
  host = request.form['host']
  hostscore = request.form['hostscore']
  guestscore = request.form['guestscore']
  g.conn.execute("UPDATE game SET hostscore = '{0}' , guestscore = '{1}' WHERE time = '{2}' AND location = '{3}'".format(int(hostscore) , int(guestscore) , str(date) , str(host)))
  return render_template("modifysuccess.html" , dict = {'username': str(adminname)})

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
   

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=true, threaded=threaded)


  run()
