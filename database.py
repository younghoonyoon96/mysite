import pymysql

# mysql과 연동하고 sql 쿼리문을 보내고 결과를 받아올수 있는 class 선언 
class MyDB:
    # 생성자 함수 
    # 매개변수 : 서버의 정보(기본값은 내컴퓨터의 DB 정보)
    def __init__(
        self, 
        _host = '127.0.0.1', 
        _port = 3306, 
        _user = 'root', 
        _pw = '', 
        _db_name = 'ubion'
    ):
        # 생성된 class에서 독립적으로 사용하려는 변수를 등록하는 과정
        self.host = _host
        self.port = _port
        self.user = _user
        self.pw = _pw
        self.db = _db_name

    # DB 서버와의 연결하고 cursor 생성 query문 전송 필요에따라 결과 값 리턴
    def sql_query(
        self, 
        _query, 
        *_data_list
    ):
        # 서버와의 연결 
        self._db = pymysql.connect(
            host = self.host, 
            port = self.port, 
            user = self.user, 
            password = self.pw, 
            db = self.db
        )
        # cursor 생성
        cursor = self._db.cursor(pymysql.cursors.DictCursor)

        cursor.execute(_query, _data_list)

        # _query가 select문이라면
        if _query.upper().lstrip().startswith("SELECT"):
            result = cursor.fetchall()
            return result
        else:
            print('Query OK!')
    def commit_db(self):
        self._db.commit()
        print('commit 완료')
        self._db.close()
        print('close 완료')