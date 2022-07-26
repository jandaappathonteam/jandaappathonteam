"""
Simple app to upload an image via a web form 
and view the inference results on the image in the browser.
"""
import argparse
import io
import os
from unittest import result
from PIL import Image
import json
import uuid
import sqlite3

import torch
from flask import Flask, render_template, request, redirect, jsonify



app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/predict", methods=["GET", "POST"])
def predict():
    # print("step00")
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

        bottlecount = 0 
        for i in datajson:
            # print(i)
            if i['name'] == "bottle":
                bottlecount = bottlecount + 1

    resultdata = {
                    "code": "200",
                    "message": "successful",
                    "count": bottlecount,
                    "url": "/images/" +  uuidfilename
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

    datalist = []
    
    for row in data:
        result = {}
        result['school'] = row[0]
        result['count'] = row[1]
        datalist.append(result)
   
    resultdic = {}
    resultdic["code"] = '200'
    resultdic["message"] = "successful"
    resultdic["total"] = str(len(datalist))
    resultdic["data"] =  datalist  

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
    app.run(host="127.0.0.1", port=args.port)  # debug=True causes Restarting with stat
