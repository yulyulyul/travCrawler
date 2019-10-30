import csv ,scrapy,json, re, pymongo
from collections import OrderedDict
from scrapy import FormRequest

from travScraper.spiders.dbinfo import mongoip, mongopwd, mongoid

conn = pymongo.MongoClient('mongodb://'+ mongoid +':'+mongopwd+'@'+mongoip, 30121)
db = conn.get_database('trav')
mongoPakage= db.get_collection('pakage')

class travel_agency(scrapy.Spider):
    name = "agencyCrawler"  # spider 이름

    outfile = open("myfile.csv", "a+", newline="")
    writer = csv.writer(outfile)

    cnt = 0;

    def start_requests(self):

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        urls = [
            'https://www.ybtour.co.kr/CMMN/header.ajax'
        ]
        self.writer.writerow(["상품명", "상품코드", "종속 메뉴코드", "메뉴코드", "항공코드", "항공사",
                              "상품 이미지", "최소 가격", "최대 가격", "최소 출발 날짜", "최대 출발 날짜"])

        for i, url in enumerate(urls):
            yield scrapy.Request(url=url, meta={'cookiejar':i} ,callback=self.allMenuParse)
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # params = {
        #     'menu': 'PKG',
        #     'dspSid': '',
        #     'evCd': ''
        # }
        #
        # # params.__setitem__('dspSid', "AADC004")
        # # params.__setitem__('evCd', "CIP1147-191105KE00")
        #
        # # params.__setitem__('dspSid', "AAAA002")
        # # params.__setitem__('evCd', "EWP2318-191026OZ00")
        #
        # # params.__setitem__('dspSid', "ABBC001")
        # # params.__setitem__('evCd', "ATF1048-191019KE00")
        #
        # params.__setitem__('dspSid', "AAAA002")
        # params.__setitem__('evCd', "EWP2228-191102OZ00")
        #
        # request = FormRequest("https://www.ybtour.co.kr/product/detailPackage.yb?",
        #                       meta={'cookiejar': 1}
        #                       , callback=self.detailPage, method='GET', formdata=params)
        # yield request
        ########################################################################################################################


    def allMenuParse(self, response):
        rdata = response.body.decode("utf-8")
        jsdata = json.loads(rdata)
        i = 0;
        for key in list(jsdata["menuList"]["allMenuList"].keys()):
            if key[-3:] == "000":
            # print("["+str(i) + " ] key : " + key + " // after : " + key[-3:])
            # self.writer.writerow([[i],[key]])
            # with open('myfile.csv', 'a') as f:
            #     f.write('key    {0}\n'.format(key))
            # f.close()

                i += 1
                params = {
                    'dspSid': '',
                    'singleTypeCd': 'G',
                    'viewListType': 'pdt_list',
                    'sortData[prop]': 'sortOrder',
                    'sortData[asc]': 'true'
                }

                params.__setitem__('dspSid', key)
                request = FormRequest("https://www.ybtour.co.kr/product/selectMasterList.ajax",
                                      meta={'cookiejar': response.meta['cookiejar']}
                                      , callback=self.MenuPage, method='POST', formdata=params)
                yield request

            if i > 3:
                break

    def MenuPage(self, response):
        rdata = response.body.decode("utf-8")
        menuData = json.loads(rdata)

        # self.writer.writerow([self.cnt])
        # self.cnt +=1

        for i in range(0, len(menuData["DATA"])):
            # print("[" + str(i) + "] : " + menuData["DATA"][i]["goodsNm"])
            # self.writer.writerow([menuData["DATA"][i]["goodsNm"],    menuData["DATA"][i]["goodsCd"],
            #                       menuData["DATA"][i]["dspSid"],      menuData["DATA"][i]["dspSidHi"],
            #                       menuData["DATA"][i]["airCd"],      menuData["DATA"][i]["airName"],
            #                       menuData["DATA"][i]["imageThum3"],  menuData["DATA"][i]["minPrice"],
            #                       menuData["DATA"][i]["maxPrice"],    menuData["DATA"][i]["minStartDt"],
            #                       menuData["DATA"][i]["maxStartDt"]])

            dspSid = str(menuData["DATA"][i]["dspSid"]).split(",").__getitem__(0)
            evCd = str(menuData["DATA"][i]["goodsCd"])+"-" + str(menuData["DATA"][i]["minStartDt"])[2:] + str(menuData["DATA"][i]["airCd"]).split(",").__getitem__(0)  + "00"
            # print("[" + str(i) + "] : " + menuData["DATA"][i]["dspSid"])
            # print("[" + str(i) + "] : " + dspSid)
            # print("[" + str(i) + "] : " + evCd + "\n")

            params = {
                'menu': 'PKG',
                'dspSid': '',
                'evCd': ''
            }

            params.__setitem__('dspSid', dspSid)
            params.__setitem__('evCd', evCd)

            request = FormRequest("https://www.ybtour.co.kr/product/detailPackage.yb?",
                                  meta={'cookiejar': response.meta['cookiejar']}
                                  , callback=self.detailPage, method='GET', formdata=params)
            yield request

    def detailPage(self, response):
        post = OrderedDict()
        smallPostList = list()
        # print(response.body.decode("utf-8"))
        goodsName = response.xpath('//*[@id="product"]/div/h3/text()').extract()
        goodsCode = response.xpath('//*[@id="product"]/div/div[1]/div[1]/dl/dd/text()').extract()

        travelPeriod = response.xpath('//*[@id="product"]/div/div[2]/div[1]/table[1]/tbody/tr[1]/td/span/text()').extract()
        airline = response.xpath('//*[@id="product"]/div/div[2]/div[1]/table[1]/tbody/tr[2]/td/div[1]/p/span[2]/text()').extract()

        travelRoutes = response.xpath('//*[@id="product"]/div/div[2]/div[1]/table[1]/tbody/tr[3]/td/div/text()').extract()
        totalPrice = response.xpath('//*[@id="priceSummary"]/text()').extract()

        departAirNum = response.xpath('///*[@id="product"]/div/div[2]/div[1]/table[1]/tbody/tr[2]/td/div[2]/div[1]/span/text()').extract()
        arriveAirNum = response.xpath('//*[@id="product"]/div/div[2]/div[1]/table[1]/tbody/tr[2]/td/div[2]/div[2]/span/text()').extract()

        detail_Itinerary  = response.xpath('//*[@id="tab_page1"]/div/div').extract()
        # // *[ @ id = "tab_page1"] / div[4] / div[1]
        # goodsCode = response.xpath('//*[@id="product"]/div/div[1]/div[1]/dl/dd/text()').extract()

        # print("상품명 : " + goodsName[0])
        # print("상품코드 : " + goodsCode[0])
        post["agency"] = "노랑풍선"
        post["goodsName"] = goodsName[0]
        post["goodsCode"] = goodsCode[0]

        str_period = str(travelPeriod[0]).strip()
        # print("여행기간 : " + str_period)
        post["period"] = str_period
        # print("항공사 : " + airline[0])
        post["airline"] = airline[0]

        # print("출국 항공번호 : " + departAirNum[0])
        # print("귀국 항공번호 : " + arriveAirNum[0])

        # print("방문도시 : " + str(travelRoutes[1]).strip())
        visitedCity = str(travelRoutes[1]).strip()
        arrVisited = list()
        # post["visitedCity"] = visitedCity
        if visitedCity.__contains__("→"):
            arrVisited = visitedCity.split("→")
        elif  visitedCity.__contains__("/"):
            arrVisited = visitedCity.split("/")
        if arrVisited.__len__() > 0:
            for a in range(0, (arrVisited.__len__() - 1)):
                arrVisited[a] = arrVisited[a].strip()+" "
                if arrVisited[a].__contains__("(") :
                    arrVisited[a] = str(arrVisited[a])[:arrVisited[a].index("(")]+" "

            if arrVisited[0] == arrVisited.__getitem__(arrVisited.__len__()-1):
                forsize = arrVisited.__len__()-2
            else:
                forsize = arrVisited.__len__()-1

            returnVal = ""
            for a in range(0 ,forsize):
                returnVal += arrVisited[a]
            post["visitedCity"] = returnVal
            returnVal = str(returnVal).replace("/", " ")
            # print("val : " + returnVal)

        Tprice = int(str(totalPrice[0]).replace(",",""))
        # print("총 비용 : " + str(Tprice))
        post["totalPrice"] = Tprice

        # print("여행 일정 : ", len(detail_Itinerary))
        # str(detail_Itinerary[0])


        spost = OrderedDict()
        sp_content_List = list()
        sp_content = OrderedDict()

        for k in range(len(detail_Itinerary)):
            day = response.xpath('//*[ @ id = "anchor_day'+ str(k+1) +'"]/h3/text()').extract()
            date = response.xpath('//*[ @ id = "anchor_day' + str(k+1) + '"]/span/text()').extract()
            if len(day) > 0:
                spost["days"] = str(day[0]).strip()
                # print("일차 : " + day[0])
            if len(date) > 0:
                if str(date[0]).__contains__("-"):
                    spost["dates"] = str(date[0])[:str(date[0]).index("-")].__str__().strip()
                else:
                    spost["dates"] = date[0]
                # print("\t날짜 - 지역 : " + date[0])

            location = response.xpath('//*[@id="tab_page1"]/div/div['+str(k+1)+']/div/div').extract()
            # print(len(location))
            locationList = list()
            locationList.clear()
            tempLoc = ""
            for c in range(len(location)):
                baseXpath = '//*[@id="tab_page1"]/div/div[' + str(k + 1) + ']/div/div[' + str(c + 1) + ']'

                tempLocation = response.xpath(baseXpath+'/h3/text()').extract()
                schedule = response.xpath(baseXpath+'/p/text()').extract()
                subSchedule = response.xpath(baseXpath+'/div[@class="box_editor"]').extract()

                imageName = response.xpath(baseXpath + '/div/div/ul/li/h5/text()').extract()
                imagePath = response.xpath(baseXpath + '/div/div/ul/li/div/div/span/img/@src').extract()
                imageText = response.xpath(baseXpath + '/div/div/ul/li/p').extract()

                # // *[ @ id = "tab_page1"] / div[3] / div[1] / div[3] / div / h3
                if len(tempLocation) > 0:
                    # print("\t\t거점 : " + tempLocation[0] + "size : " + str(len(tempLocation)))
                    if (tempLoc != tempLocation[0]) or (len(tempLocation) > 0):
                        # print("in if..")
                        # print("tempLoc : " + tempLoc)

                        if len(tempLoc) != 0:
                            includeData = OrderedDict()
                            tempLoc = str(tempLoc).strip()
                            # print("tempLoc : " + tempLoc)
                            # print('sp_content["Description"] : ' + sp_content["Description"])
                            includeData[tempLoc] = sp_content_List
                            locationList.append(includeData)
                            # print(json.dumps(locationList, ensure_ascii=False, indent="\t"))

                        # print("tempLoc : "+tempLoc + "  tempL[0] : " + tempLocation[0])

                        sp_content_List = list()
                        # sp_content_List.clear()

                        sp_content = OrderedDict()
                        tempLoc = tempLocation[0]
                        # sp_content[tempLoc]={}


                    # print(subSchedule)

                if len(schedule) > 0:
                    # print("\t\t일정 설명 : " + schedule[0]+ "size : " + str(len(schedule)))
                    sp_content["Description"] = schedule[0]
                else:
                    sp_content["Description"] = None

                if len(subSchedule) > 0:
                    scheduleTxt = re.sub('<[^>]*>', '', str(subSchedule[0])).strip()
                    # print("\t\t추가 설명 : " + scheduleTxt)
                    sp_content["detail_Description"] = scheduleTxt
                else:
                    sp_content["detail_Description"] = None

                # print("\t\t\t추가 설명 : " + nohtmlstr.strip())
                if len(imageName) > 0:
                    for aa in range(len(imageName)):
                        # print("\t\t사진 이름 : " + imageName[aa])
                        sp_content["pic_name"] = imageName[aa]

                        pathList = list()
                        for bb in range(len(imagePath)):
                            pathList.append(imagePath[bb])
                            # print("\t\t사진 경로 : " + imagePath[bb])
                        sp_content["pic_path"] = pathList

                        if len(imageText) > 0:
                            imgDescription = re.sub('<[^>]*>', '', str(imageText[aa])).strip()
                            # print("\t\t사진 설명 : " + imgDescription)
                            sp_content["pic_des"] = imgDescription
                else:
                    sp_content["pic_name"] = None
                    sp_content["pic_path"] = None
                    sp_content["pic_des"] = None


                if ((sp_content["Description"] == None) and (sp_content["detail_Description"] == None) and (sp_content["pic_name"] == None) and (sp_content["pic_path"] == None) and (sp_content["pic_des"] == None)) == False:
                    sp_content_List.append(sp_content)
                sp_content = OrderedDict()


            # print(locationList)
            # print(json.dumps(locationList, ensure_ascii=False, indent="\t"))


            includeData2 = OrderedDict()
            tempLoc = str(tempLoc).strip()
            includeData2[tempLoc] = sp_content_List
            locationList.append(includeData2)

            spost["loaction"] = locationList
            # print(json.dumps(spost, ensure_ascii=False, indent="\t"))

            # 작업중.. 자꾸 마지막 노드가 똑같이 들어가는 것들이 있음. 그런걸 쳐내야함.
            if smallPostList.__len__() > 0:
                jsonToStr2 = json.dumps(spost, ensure_ascii=False, indent="\t")
                strToDict2 = json.loads(jsonToStr2)

                if smallPostList.__getitem__(smallPostList.__len__() - 1)["days"] != strToDict2["days"] :
                    smallPostList.append(strToDict2)

            elif smallPostList.__len__() == 0:
                jsonToStr = json.dumps(spost, ensure_ascii=False, indent="\t")
                strToDict = json.loads(jsonToStr)
                smallPostList.append(strToDict)

        post["small_post"] = smallPostList
        postJson = json.dumps(post, ensure_ascii=False, indent="\t")
        print(postJson)
        # mongoPakage.insert(post)
    
    def close(self):
        self.outfile.close()
        print("-----Check to see if this is closed-----")


