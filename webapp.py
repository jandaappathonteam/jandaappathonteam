"""
Simple app to upload an image via a web form 
and view the inference results on the image in the browser.
"""
import argparse
# from asyncio.windows_events import NULL
# from curses.ascii import NUL
import io
import os
from unittest import result
from PIL import Image
import json
import uuid
import sqlite3
import time

import torch
from flask import Flask, render_template, request, redirect, jsonify, session



app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

# @app.route('/login/<name>', methods=['Get'])
# def login(name):
#     print(name)
#     session['username'] = name
#     print(session['username'] )
#     return "welcome " + name

@app.route("/predict/<name>", methods=["GET", "POST"])
def predict(name):
    print("2022072701")
    
    resultdata = {}
    if request.method == "POST":
        if "file" not in request.files:         
            return redirect(request.url)
        file = request.files["file"]
        if not file:
            return
        
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))
        results = model(img, size=640)
        strResults = str(results)

        # for debugging
        # data = results.pandas().xyxy[0].to_json(orient="records")
        # return data

        uuidfilename = str(uuid.uuid1()) +".jpg"

        results.render()  # updates results.imgs with boxes and labels
        for img in results.imgs:
            img_base64 = Image.fromarray(img)           
            # img_base64.save("static/image0.jpg", format="JPEG")
            img_base64.save("static/images/" + uuidfilename, format="JPEG")

        data = results.pandas().xyxy[0].to_json(orient="records")
        # print (type(data))
        datajson = json.loads(data)
        # print(type(datajson))

        # statis = {}
        # for i in datajson:
        #     # print(i)
        #     name = i['name']
        #     if statis.__contains__(name):
        #         statis[name] = statis[name] + 1
        #     else:
        #         statis[name] = 1
        # arrayData = []
        # for v in statis.keys():
        #     arrayData.append({"class": v, "value": statis[v]})

        # count how many bottles in the AI detection result
        bottlecount = 0
        for i in datajson:
            # print(i)
            if i['name'] == "bottle":
                bottlecount = bottlecount + 1
        
        #update db
     
        if name is not None: 
            sqlcommand = "select * from students where name='" + name + "' LIMIT  1"
            resultlist = getDatafromDB(sqlcommand)
            print(resultlist)
            conn = sqlite3.connect('student.db')
            cur = conn.cursor()
            sqlcomm = "insert into students values('" + resultlist[0]['name'] +"','" + resultlist[0]['class'] +"','" + resultlist[0]['school'] +"',"\
                 + str(bottlecount) + ",'" + time.strftime('%Y-%m-%d', time.localtime()) + "')" 
            # print(sqlcomm)
            cur.execute(sqlcomm)
            conn.commit()
        else:
            conn = sqlite3.connect('student.db')
            cur = conn.cursor()
            sqlcomm = "insert into students values('Jiayu','10','Plano West Senior High School',"\
                 + str(bottlecount) + ",'" + time.strftime('%Y-%m-%d', time.localtime()) + "')" 
            # print(sqlcomm)
            cur.execute(sqlcomm)
            conn.commit()

        # data = cur.fetchall()
        conn.close()

        resultdata = {
                        "code": "200",
                        "message": "successful",
                        "count": bottlecount,
                        "url": "/images/" +  uuidfilename
                    }
    else:
        resultdata = {
                        "code": "200",
                        "message": "not using post method",
                        "count": 0,
                        "url": "0"
                    }

    return resultdata
    # return redirect("static/image0.jpg")
    # return render_template("index.html")


#DB operation
def getDatafromDB(sqlcommand):
    
    conn = sqlite3.connect('student.db')
    cur = conn.cursor()
    cur.execute(sqlcommand)

    data = cur.fetchall()
    conn.close()
    datalist = []
    
    for row in data:
        result = {}
        result['name'] = row[0]
        result['class'] = row[1]
        result['school'] = row[2]
        result['count'] = row[3]
        datalist.append(result)

    return datalist

@app.route('/getAnUser/<name>', methods=['GET'])
def getAnUser(name):

    sqlcomm = "select * from students where name='" + name + "'"
    jsonData = getDatafromDB(sqlcomm)
   
    resultdic = {}
    resultdic["code"] = '200'
    resultdic["message"] = "successful"
    resultdic["total"] = str(len(jsonData))
    resultdic["data"] =  jsonData     

    return jsonify(resultdic)

@app.route('/getUsers', methods=['GET'])
def getUsers():
    
    sqlcomm = "select * from students"
    jsonData = getDatafromDB(sqlcomm)
   
    resultdic = {}
    resultdic["code"] = '200'
    resultdic["message"] = "successful"
    resultdic["total"] = str(len(jsonData))
    resultdic["data"] =  jsonData     

    return jsonify(resultdic)

@app.route('/gettotal/<schoolname>', methods=['Get'])
def getTotal(schoolname):
    
    # schoolname = request.args.get('school')

    conn = sqlite3.connect('student.db')
    cur = conn.cursor()
    sqlcomm = "select school, sum(bottolcount) as total from students group by school having school='"+ schoolname +"'"
    cur.execute(sqlcomm)

    data = cur.fetchall()
    conn.close()

    result = {}
    
    for row in data:
        result = {}
        result['school'] = row[0]
        result['count'] = row[1]
        
   
    resultdic = {}
    resultdic["code"] = '200'
    resultdic["message"] = "successful"
    resultdic["count"] = result['count']
    resultdic["school"] = result['school']  

    return jsonify(resultdic)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app exposing yolov5 models")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()

    # model = torch.hub.load(
    #     "ultralytics/yolov5", "yolov5x", pretrained=True, force_reload=True, autoshape=True
    # )  # force_reload = recache latest code

    model = torch.hub.load(
        "yolov5-master", "yolov5l", pretrained=True, source='local', force_reload=True, autoshape=True
    )  

    model.eval()
    app.debug = True
    # app.secret_key = "affedasafafqwe"
    app.run(host="127.0.0.1", port=args.port)  # debug=True causes Restarting with stat
