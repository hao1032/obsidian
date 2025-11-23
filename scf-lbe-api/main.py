import json
from llm import LLM
import jmespath

json_str = r"""
{
    "code": 0,
    "msg": null,
    "data": {
        "id": 175,
        "name": "美国数学测评（AMC10&12）",
        "description": "全球知名数学测评-美国AMC系列。AMC10/12分为A卷与B卷，难度同等，学生可选择任一参加，或都参加。",
        "thumb": "http://seed-static.seedasdan.com/wordpress/2022/08/AMC10121.jpg",
        "startDate": "2025-11-14",
        "opened": false,
        "hot": false,
        "frequency": null,
        "locationList": [
            "全国各合作学校校内"
        ],
        "tagList": null,
        "contactQrCode": null,
        "signupProjectId": null,
        "nameEn": "American Mathematics Competition (AMC10/12)",
        "descriptionEn": "Global authoritative youth math challenge",
        "priority": null,
        "sortSequence": 100,
        "agePeriod": null,
        "endDate": "2025-10-27 23:59:59",
        "subjectId": 6,
        "qa": [
            {
                "question": "如何更改注册信息？",
                "answer": "登录微信“阿思丹国际学术挑战”小程序 -“我的报名”- 点击“个人资料”可修改个人信息（如需修改手机号，点击“我的”- 账号安全处完成修改）。",
                "hidden": false
            },
            {
                "question": "AMC10和AMC12的参赛资格？",
                "answer": "AMC10：以活动当天为准，10年级（高一）且17.5岁以下年级/年龄学生；AMC12：以活动当天为准，12年级（高三）且19.5岁以下年级/年龄学生。",
                "hidden": false
            },
            {
                "question": "何时收到考试细则及流程说明？",
                "answer": "正式活动前3天左右（具体以实际发出时间为准）将以邮件和短信的形式发送活动说明等重要事项至报名预留的邮箱和手机号，届时请注意查收！",
                "hidden": false
            },
            {
                "question": "可以退费吗？",
                "answer": "同学报名缴费之后，由于临时有事可以申请退出。在报名截止日之前申请，将扣除报名费的25%作为学术材料费及服务费；报名截止日之后申请，将不予退费。",
                "hidden": false
            },
            {
                "question": "可以使用计算器吗？",
                "answer": "禁止使用任何形式的计算器。",
                "hidden": false
            },
            {
                "question": "何时公布奖项？",
                "answer": "具体开放时间根据国外MAA组委会公布后另行通知，所有成绩将在“阿思丹国际学术挑战”微信小程序上公布。",
                "hidden": false
            },
            {
                "question": "如何查询成绩和下载电子证书？",
                "answer": "成绩公布后，登录微信“阿思丹国际学术挑战”小程序 -“我的报名”- 点击对应项目-“成绩查询”/“证书下载”，进行成绩查询和电子证书下载。",
                "hidden": false
            }
        ],
        "moduleList": [
            {
                "name": "报名须知/Requirement",
                "itemList": [],
                "content": "<p><span style=\"font-weight: bold;\">1. 仅限在中国大陆地区就读的学生报名。非中国大陆地区学生如需报名请联系当地组委会。</span></p><p><span style=\"font-weight: bold;\">Registration is only open to students studying in mainland China. Students outside mainland China&nbsp; &nbsp; &nbsp; &nbsp; who wish to register should contact the local organizing committee.</span></p><p><span style=\"font-weight: bold;\"><span style=\"color: rgb(231, 76, 60);\">2.&nbsp;</span></span><span style=\"color: rgb(231, 76, 60);\">根据美国MAA组委会最新考试规定，全球目前仅允许线下考点考试，不再支持居家线上考试。对于就读学校未设立线下考点的学生，若因考位不足无法选到其他考点，将无法参加当期考试，考生须明确知晓并接受后再报名。</span></p><p><span style=\"color: rgb(231, 76, 60);\">According to the latest exam regulations from the MAA organizing committee in the United States, only in-person exam centers are allowed worldwide, and online at-home exams are no longer available. For students whose schools do not offer an in-person exam center, you are unable to register due to limited availability of exam spots, so you will not be able to participate in this exam session. Please read this announcement carefully and understand the rules before registering.</span></p>",
                "hidden": false
            },
            {
                "name": "简介",
                "itemList": [
                    {
                        "content": "http://seed-academy.oss-cn-beijing.aliyuncs.com/wx/d6cb19bf-5c65-4cbf-968e-7996e9648577.png",
                        "type": 2,
                        "toProjectId": null
                    }
                ],
                "content": "<p><span style=\"font-weight: bold; color: rgb(249, 150, 59);\">美国数学测评 (AMC) </span>由美国数学协会 (MAA) 举办，目前每年全球超过 6000 所学校的 30 万名同学参加，是全球最有影响力的青少\n年数学测评活动之一。美国数学测评规划图如下图所示：</p><p>AMC10 主要面向 10 年级及以下同学，AMC12 面向12年级及以下同学；在AMC10/12中获得优异成绩的同学，将被邀请参加美国数学测评邀请挑战AIME。\n\nUSAMO/USAJMO 为美国数学奥林匹克选拔美国国家队的挑战，胜出同学将代表美国参加全球最高数学挑战IMO。&nbsp;</p><p>美国AMC数学测评系列被誉为“ 世界名校的通行证 ”。部分学校的网申系统，比如麻省理工大学、加州理工大学、布朗大学、卡耐基梅隆大学，都需要专门填写AMC数学测评成绩，足以见大学对该奖项的重视。&nbsp;&nbsp;<br></p><p><br></p>",
                "hidden": false
            },
            {
                "name": "项目规则",
                "itemList": [],
                "content": "<p><span style=\"font-weight: bold; color: rgb(249, 150, 59);\">语言：</span>中英文双语&nbsp;</p><p><span style=\"color: rgb(249, 150, 59); font-weight: bold;\">时间：\n</span>• A 卷：2025 年 11 月&nbsp; 6&nbsp; 日（周四）17:00-18:15（75 分钟）</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; • B 卷：2025 年 11 月 14 日（周五）17:00-18:15（75 分钟）</p><p><span style=\"font-weight: bold; color: rgb(249, 150, 59);\">地点：</span>线下</p><p><span style=\"font-weight: bold; color: rgb(249, 150, 59);\">资格：</span>（年龄截止至测评活动当天）&nbsp;</p><p>• AMC 10：10 年级（高一）且 17.5 岁以下年级 / 年龄学生&nbsp;</p><p>• AMC 12：12 年级（高三）且 19.5 岁以下年级 / 年龄学生</p><p><span style=\"font-weight: bold; color: rgb(249, 150, 59);\">形式：</span>个人，25 道单项选择题</p><p><span style=\"font-weight: bold; color: rgb(249, 150, 59);\">考核内容：</span>AMC10 通常涵盖初三和高一数学课程内容，包括初等代数、基础几何学（勾股定理、面积体积公式等）、\n初等数论和概率问题，不包括三角函数、高等代数和高等几\n何学知识。AMC12 涵盖以上全部内容，但不包括微积分&nbsp;</p><p><span style=\"font-weight: bold; color: rgb(249, 150, 59);\">评分标准：</span>答对一题得 6 分，未答得 1.5 分，答错不扣分，\n满分 150 分&nbsp;</p><p><span style=\"font-weight: bold; color: rgb(249, 150, 59);\">A 卷 / B 卷说明：</span>AMC10/AMC12 的 A 卷和 B 卷是不同\n的试卷，但同等难度和范围，同学可以任选 A 或 B 卷参加\n考试，也可以 A 和 B 卷考试都参加，最终取 A 卷和 B 卷的\n最高个人成绩参与评奖排名和晋级 AIME&nbsp; &nbsp;</p><p>注：\n\n\n\n\n\n                在读年级参考下图填写\n\n</p><p><img src=\"https://attach.seedasdan.com/STEM/GradeSystem.png\" style=\"max-width:100%;\"></p><p><span style=\"color: rgb(249, 150, 59); font-weight: bold;\">报名截止时间：</span></p><p>A卷：2025年10月27日</p><p>B卷：2025年11月4日</p>",
                "hidden": false
            }
        ],
        "detailUrl": "http://www.seedasdan.asia/en/amc10-en/",
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
    expression = "data.moduleList[?(@.name=='项目规则')].content"
    data = json.loads(json_str)
    matches = jmespath.search(expression, data)
    print(matches)

    llm = LLM(key='sk-sexuqwmujquabfnxkwohxvdsiisklpogzivohpqdwogjclfi')
    r = llm.test_time('AMC 10 A', matches[0])
    print(r)