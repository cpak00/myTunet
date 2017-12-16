import requests
from bs4 import BeautifulSoup
import chardet
import getpass
import urllib


def get_hm_wk_info(userid, passwd):
    data = {'userid': userid, 'userpass': passwd, 'submit1': '登录'}
    login_url = 'https://learn.tsinghua.edu.cn/MultiLanguage/lesson/teacher/loginteacher.jsp'
    cookies = requests.post(url=login_url, data=data).cookies
    if 'THNSV2COOKIE' not in cookies:
        raise Exception
        return
    mainCourse = 'http://learn.tsinghua.edu.cn/MultiLanguage/lesson/student/MyCourse.jsp?language=cn'
    html_text = requests.get(url=mainCourse, cookies=cookies).text
    charset = chardet.detect(html_text.encode())
    html_bs = BeautifulSoup(html_text, 'lxml')
    table = html_bs.find("table", id='info_1')
    hm_wk_url = 'http://learn.tsinghua.edu.cn/MultiLanguage/lesson/student/hom_wk_brw.jsp?'
    hm_wk_info = []
    for tr in table.find_all('tr'):
        try:
            course = []
            if tr.a is not None:
                course.append(tr.a.get_text().strip())
                if '实验室科研探究' in tr.a.get_text():
                    continue
                tds = tr.find_all('td')
                for td in tds:
                    try:
                        if td is not None and '作业' in td.get_text():
                            if int(td.span.get_text()) != 0:
                                href = (tr.a['href'])
                                course_id = urllib.parse.urlparse(href)[4]
                                # print(tr.a.get_text() + ' ' + course_id)
                                hm_wk = BeautifulSoup(
                                    requests.get(
                                        url=hm_wk_url + course_id,
                                        cookies=cookies).text,
                                    'lxml').find_all(id='table_box')[1]
                                for tr in hm_wk.find_all('tr'):
                                    info = []
                                    for td in tr.find_all('td'):
                                        info.append(td.get_text().strip())
                                    if '尚未提交' in info:
                                        course.append(info[0:3:2])
                    except Exception as e:
                        continue
            if (len(course) > 1):
                hm_wk_info.append(course)
        except Exception as e:
            if (len(course) > 1):
                hm_wk_info.append(course)
            continue

    return (hm_wk_info)


if __name__ == '__main__':
    userid = input('输入用户名: ')
    userpass = getpass.getpass('请输入密码: ')
    print(get_hm_wk_info(userid, userpass))
