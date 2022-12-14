"""
Simple app to upload an image via a web form 
and view the inference results on the image in the browser.
"""
import argparse

import io
import os
from unittest import result
from PIL import Image
from PIL import ImageFile

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

# 压缩图片文件
def compress_image(outfile, mb=5, quality=85, k=0.9): # 通常你只需要修改mb大小
    """不改变图片尺寸压缩到指定大小
    :param outfile: 压缩文件保存地址
    :param mb: 压缩目标，KB
    :param k: 每次调整的压缩比率
    :param quality: 初始压缩比率
    :return: 压缩文件地址，压缩文件大小
    """ 
    o_size = os.path.getsize(outfile) // 1024  # 函数返回为字节，除1024转为kb（1kb = 1024 bit）
    print('before_size:{} after_size:{}'.format(o_size, mb))
    if o_size <= mb:
        return outfile
    
    ImageFile.LOAD_TRUNCATED_IMAGES = True  # 防止图像被截断而报错
    
    while o_size > mb:
        im = Image.open(outfile)
        x, y = im.size
        # out = im.resize((int(x*k), int(y*k)), Image.ANTIALIAS)  # 最后一个参数设置可以提高图片转换后的质量
        out = im.resize((int(x*k), int(y*k)), Image.LANCZOS)
        try:
            out.save(outfile, quality=quality)  # quality为保存的质量，从1（最差）到95（最好），此时为85
        except Exception as e:
            print(e)
            break
        o_size = os.path.getsize(outfile) // 1024
    return outfile



@app.route("/predict/<name>", methods=["POST"])
def predict(name):
    print("2022072701")
    
    resultdata = {}
    if request.method == "POST":
        if "file" not in request.files:         
            return redirect(request.url)
        file = request.files["file"]
        print(type(file))
        if not file:
            return
        
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))
        results = model(img, size=640)
        strResults = str(results)

       
        uuidfilename = str(uuid.uuid1()) +".jpg"

        results.render()  # updates results.imgs with boxes and labels
        for img in results.imgs:
            img_base64 = Image.fromarray(img)       
           
            img_base64.save("static/images/" + uuidfilename, format="JPEG")

        data = results.pandas().xyxy[0].to_json(orient="records")
        # print (type(data))
        datajson = json.loads(data)
        
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


@app.route("/mitpredict/<name>", methods=["POST"])
def mitpredict(name):
    print("2022072702")
    
    resultdata = {}

    if request.method == "POST":        
        file_bytes = request.data
        print(type(file_bytes))
        with open("mit-client-src1.jpg","wb") as f:
            f.write(file_bytes)
        
        #compress image
        compressedfile = compress_image("mit-client-src1.jpg",mb=90)

        # img_bytes = file.read()
        # img = Image.open(io.BytesIO(file_bytes))
        img = Image.open("mit-client-src1.jpg")
        # print(type(img))
        results = model(img, size=640)
        strResults = str(results)
        # print(strResults) 

     
        uuidfilename = str(uuid.uuid1()) +".jpg"

        results.render()  # updates results.imgs with boxes and labels
        for img in results.imgs:
            img_base64 = Image.fromarray(img)           
            # img_base64.save("static/image0.jpg", format="JPEG")
            img_base64.save("static/images/" + uuidfilename, format="JPEG")

        data = results.pandas().xyxy[0].to_json(orient="records")
        # print (type(data))
        datajson = json.loads(data)
        
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
    app.run(host="127.0.0.1", port=args.port)  # debug=True causes Restarting with stat
