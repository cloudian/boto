# -*- coding: utf-8 -*-

from random import choice, randint

class S3SelectData(object):
    def __init__(self, type, nfields=10, nrecords=10, fd=',', rd='\n', qc='"', qec='"', hdr=None, fielddic={}):
        # type:    "csv" or "json"
        # nfields:  number of columns        (CSV/JSON)
        # nrecords: number of records        (CSV/JSON)
        # fd:      field delimiter           (CSV)
        # rd:      record delimiter          (CSV)
        # qc:      quote character           (CSV)
        # qec:     quote escape character    (CSV)
        # hdr:     None or True              (CSV)
        self.type = type
        self.nfields = nfields
        self.nrecords = nrecords
        self.fd = fd
        self.rd = rd
        self.qc = qc
        self.qec = qec
        self.hdr = hdr
        self.fieldvals = {}      # fielddic => {"int":[0,1], "single": [2,3], "multi": [4,5], "string": [6,7]}
        for vtype, posL in fielddic.iteritems():
            for pos in posL:
                self.fieldvals[pos] = vtype
        self.keyL = []
        if type == "json":
            for num_field in range(self.nfields):
                kname = self.gen_key()
                self.keyL.append(kname)

    def choose_one_of(self, seq):
        return choice(seq)

    def choose_count_of(self, seq, count):
        lseq = len(seq)
        choosen = []
        for i in xrange(count):
            choosen.append(seq[randint(0,lseq-1)])
        if isinstance(seq, str):
            return ''.join(choosen)
        elif isinstance(seq, unicode):
            return u"".join(choosen)
        else:
            # Other sequences can return as list
            return choosen

    def gen_field(self, valtype=None):
        l = randint(1, 20)
        i_field = self.choose_count_of("0123456789", l)
        m_field = choice([u"漢字", u"金", u"日本語", u"2012年2月27日",
                          u"誕生日", u"金曜日", u"カナ", u"名前", u"あ う",
                          u"犬", u"猿たち", u"ひらがな", u"住所", u"電話番号"])
        l = randint(1, 20)
        s_field = self.choose_count_of("0123456789abcdefghijklmnopqrstuvwxyzABCZ ", l)
        if valtype == "int":
            return i_field
        elif valtype == "single":
            return s_field
        elif valtype == "multi":
            return m_field
        elif valtype == "string":
            return choice([m_field, s_field])
        else:
            return choice([m_field, s_field, i_field])

    def gen_key(self):
        l = randint(1, 10)
        kname = self.choose_count_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", l)
        return kname

    def gen_record(self, num_record):
        """
        JSON format is like this:
        {
            "id":"1",
            "first_name":"Steven",
            "last_name":"Thompson",
            "email":"sthompson0@hoge.com",
            "gender":"Male",
            "ip_address":"1.2.3.4"
        }
        {
            "id":"2",
            "first_name":"Doris",
            "last_name":"Daniels",
            "email":"ddaniels1@hage.gov",
            "gender":"Female",
            "ip_address":"5.6.7.8"
        }
        """

        record = ''
        if self.type == 'json':
            record += '{\n'
        for num_field in range(self.nfields):
            if self.type == 'json':
                record += '\t'
                record += '"' + self.keyL[num_field] + '"'
                record += ':'
                if self.fieldvals.has_key(num_field):
                    val = self.gen_field(valtype=self.fieldvals[num_field])
                else:
                    val = self.gen_field()
                record += '"' + val + '"'
                record += '\n'
            else:
                if self.hdr is not None and num_record == 0:
                    # header field
                    field = self.gen_key()
                else:
                    if self.fieldvals.has_key(num_field):
                        field = self.gen_field(valtype=self.fieldvals[num_field])
                    else:
                        field = self.gen_field()
                if self.qc is not None:
                    field = self.qc + field + self.qc
                record += field
                if num_field < self.nfields - 1:
                    record += self.fd
        if self.type == 'json':
            record += '}'
        return record

    def gen_data(self, fp):
        for num_record in range(self.nrecords):
            record = self.gen_record(num_record)
            fp.write(record.encode('utf-8'))
            fp.write(self.rd)

