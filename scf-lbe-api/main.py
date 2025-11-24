import json
import os

from llm import LLM
import jmespath

json_str = r"""
{
  "code": 0,
  "msg": null,
  "data": {
    "id": 162,
    "name": "美国数学测评 (AIME)",
    "description": "高难度的数学测评活动，AMC10 和 AMC12 成绩优异的选手可以进入 AIME",
    "thumb": "http://seed-static.seedasdan.com/wordpress/2018/01/30818542321.jpg",
    "startDate": "2026-02-06",
    "opened": false,
    "hot": false,
    "frequency": null,
    "locationList": [
      "在线"
    ],
    "tagList": null,
    "contactQrCode": null,
    "signupProjectId": null,
    "nameEn": "AIME",
    "descriptionEn": "Participants of AMC10 and AMC12 with high scores in China can enter AIME",
    "priority": null,
    "sortSequence": null,
    "agePeriod": "AMC10/12表现优异选手方可晋级",
    "endDate": "2026-01-27 23:59:59",
    "subjectId": 6,
    "qa": [
      {
        "question": "如何更改注册信息？",
        "answer": "登录微信“阿思丹”小程序 -“我的阿思丹”- 点击“个人资料”可修改个人信息（如需修改手机号，点击“我的阿思丹”- 账号安全处完成修改）。",
        "hidden": false
      },
      {
        "question": "何时收到考试细则及流程说明？",
        "answer": "组委会将以邮件的形式发送考试细则和流程说明等重要事项至报名所预留的邮箱，届时请注意查收！",
        "hidden": false
      },
      {
        "question": "可以退费吗？",
        "answer": "同学报名缴费之后，由于临时有事可以申请退出。在报名截止日之前申请，将扣除报名费的25%作为学术材料费及服务费；报名截止日之后申请，将不予退费。",
        "hidden": false
      },
      {
        "question": "可以使用计算器吗？",
        "answer": "不允许使用任何计算器。",
        "hidden": false
      },
      {
        "question": "如何查询成绩和下载电子证书？",
        "answer": "成绩公布后，登录微信“阿思丹”小程序 -“我的阿思丹”-“参与项目/Program”- 点击对应项目-“成绩查询”/“证书下载”，进行成绩查询和电子证书下载。",
        "hidden": false
      },
      {
        "question": "成绩大概多久公布？",
        "answer": "成绩约在考后6-8周进行公布，具体公布时间会到时进行通知。",
        "hidden": false
      }
    ],
    "moduleList": [
      {
        "name": "简介",
        "itemList": [],
        "content": "\u003Cp\u003E\u003Cspan style=\"font-weight: bold;\"\u003E美国数学测评 (AMC) \u003C/span\u003E由美国数学协会 (MAA) 举办，目前每年全球超过 6000 所学校的 30 万名同学参加，是全球最有影响力的青少年数学测评活动之一。美国数学测评包括了 AMC8、AMC10/12、AIME、USAMO/USAJMO，其中 AMC8 主要面向 8 年级（初二）以下的初中和小学高年级学生；AMC10/12 主要面向 10 年级（高一）和 12 年级（高三）以下的高中生；AIME 主要是面向AMC10/12 优秀学生，为美国数学奥林匹克 USAMO/USAJMO 和美国数学奥林匹克国家队的选拔。\u003Cbr\u003E\u003C/p\u003E\u003Cp\u003E本活动仅邀请在AMC10/12中表现优异的选手参加。\u003C/p\u003E",
        "hidden": false
      },
      {
        "name": "时间",
        "itemList": [],
        "content": "\u003Cp\u003E\u003Cspan style=\"font-weight: bold;\"\u003E1. 时间/Time：\u003C/span\u003E\u003C/p\u003E\u003Cp\u003EAIME I 时间：2026年2月6日（周五）13:00-16:00（暂定）\u003C/p\u003E\u003Cp\u003EAIME II 时间：2026年2月12日（周四）13:00-16:00（暂定）&nbsp;&nbsp;\u003C/p\u003E\u003Cp\u003E\u003Cspan style=\"font-weight: bold;\"\u003E2. 形式/Form：\u003C/span\u003E线上/Online\u003C/p\u003E",
        "hidden": false
      }
    ],
    "detailUrl": "http://www.seedasdan.org/amc12/",
    "isCollect": false,
    "receiveList": [],
    "availableCoupons": false,
    "followWechat": false,
    "category": "STEM"
  },
  "success": true
}
"""


if __name__ == '__main__':
    expression = "data.moduleList[?(@.name=='时间')].content"
    data = json.loads(json_str)
    matches = jmespath.search(expression, data)
    print(matches)

    # llm = LLM(key='sk-sexuqwmujquabfnxkwohxvdsiisklpogzivohpqdwogjclfi')
    # r = llm.test_time('AIME Ⅰ', matches[0])
    # print(r)

    print(os.environ)