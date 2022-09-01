import datetime
import io
import logging
import os
import unittest

import numpy
import pint

if __name__ == "__main__":
    import setup

from textio import DataFrame
from textio import dirmaster
from textio import header
from textio import load
from textio import las

class TestDataFrame(unittest.TestCase):

    def test_init(self):

        df = DataFrame()
        self.assertEqual(len(df.heads),0,"Initialization of DataFrame Headers has failed!")
        self.assertEqual(len(df.running),0,"Initialization of DataFrame Headers has failed!")

        df = DataFrame(col1=[],col2=[])
        self.assertEqual(len(df.heads),2,"Initialization of DataFrame Headers has failed!")
        self.assertEqual(len(df.running),2,"Initialization of DataFrame Headers has failed!")

        df = DataFrame()

        df["col1"] = []
        df["col2"] = []
        df["col3"] = []

        self.assertEqual(len(df.heads),3,"Initialization of DataFrame Headers has failed!")
        self.assertEqual(len(df.running),3,"Initialization of DataFrame Headers has failed!")

        a = numpy.array([1,2,3.])
        b = numpy.array([4,5,6.])

        df = DataFrame(col0=a,col1=b)

        self.assertCountEqual(df.heads,["col0","col1"],"Initialization of DataFrame Running has failed!")

        df["col0"] = b
        df["col1"] = a

        numpy.testing.assert_array_equal(df["col0"],b)
        numpy.testing.assert_array_equal(df["col1"],a)

    def test_col_astype(self):

        a = numpy.array([1,2,3,4,5])
        b = numpy.array([1.,3.4,numpy.nan,4.7,8])
        c = numpy.array([datetime.datetime.today(),datetime.datetime(2022,2,2),datetime.datetime(2022,1,2),datetime.datetime(2021,12,2),None])
        d = numpy.array(["1.","","5.7","6",""])
        e = c.astype("datetime64")

        df = DataFrame(a=a,b=b,c=c,d=d,e=e)

        for dtype in ("int","str","float"):
            df['a'] = df['a'].astype(dtype)

        bb = [
            numpy.array([1,3,-99999,4,8]),
            numpy.array(["1","3","","4","8"]),
            numpy.array([1.,3.,numpy.nan,4.,8.]),
            ]

        for index,dtype in enumerate(("int","str","float")):
            df['b'] = df['b'].astype(dtype)
            numpy.testing.assert_array_equal(df['b'].vals,bb[index])

        for dtype in ("str","datetime64[D]"):
            df['c'] = df['c'].astype(dtype)

        for dtype in ("str","int","float"):

            if dtype=="int":
                df['d'] = df['d'].fromstring(dtype="int",regex=r"[-+]?\d+\b")
                df['d'] = df['d'].astype(dtype)
            else:
                df['d'] = df['d'].astype(dtype)

        for dtype in ("str","datetime64[D]"):
            df['e'] = df['e'].astype(dtype)

    def test_representation_methods(self):

        a = numpy.random.randint(0,100,20)
        b = numpy.random.randint(0,100,20)

        df = DataFrame(a=a,b=b)

    def test_add_attrs(self):

        df = DataFrame(col0=[],col1=[])

        with self.assertRaises(AttributeError):
            df.name = "main_data"

        with self.assertRaises(AttributeError):
            df.name = "other_data"
            
        with self.assertRaises(AttributeError):
            print(df.name)

    def test_container_methods(self):

        df = DataFrame()

        a = numpy.random.randint(0,100,10)
        b = numpy.random.randint(0,100,10)

        df['a'] = a
        df['b'] = b

    def test_str2col(self):

        head = "first name\tlast name"

        full_names = numpy.array(["elthon\tsmith","bill\tgates\tjohn"])

        df = DataFrame(head=full_names)
        # print('\n')
        # print(df)

        df.str2col("head",delimiter="\t")

        self.assertEqual(df.heads,["head_0","head_1","head_2"],
            "Splitting headers while splitting col_ has failed!")
        numpy.testing.assert_array_equal(df["head_0"],numpy.array(["elthon","bill"]))
        numpy.testing.assert_array_equal(df["head_1"],numpy.array(["smith","gates"]))
        numpy.testing.assert_array_equal(df["head_2"],numpy.array(["","john"]))

        # print(df)

    def test_col2str(self):

        names = numpy.array(["elthon","john","tommy"])
        nicks = numpy.array(["smith","verdin","brian"])

        df = DataFrame(names=names,nicks=nicks)
        
        col_ = df.col2str(["names","nicks"])

        numpy.testing.assert_array_equal(col_.vals,
            numpy.array(["elthon smith","john verdin","tommy brian"]))

    def test_tostruct(self):

        names = numpy.array(["elthon","john","tommy"])
        lasts = numpy.array(["smith","verdin","brian"])
        ages = numpy.array([23,45,38])

        df = DataFrame(names=names,lasts=lasts,ages=ages)

        arr_ = df.tostruct()

        numpy.testing.assert_array_equal(arr_[0].tolist(),('elthon', 'smith', 23))

    def test_sort(self):

        A = numpy.array([ 6 , 6 , 2 , 2 , 3 , 5 , 3 , 4 , 3 , 1 , 2 , 1 ])
        B = numpy.array(["A","B","C","D","D","C","C","C","C","E","F","F"])

        df = DataFrame(A=A,B=B)

        df = df.sort(('A',))

        numpy.testing.assert_array_equal(df["A"].vals,
            numpy.array([1,1,2,2,2,3,3,3,4,5,6,6]))

        numpy.testing.assert_array_equal(df["B"].vals,
            numpy.array(["E","F","C","D","F","D","C","C","C","C","A","B"]))

        df = DataFrame(A=A,B=B)

        df = df.sort(('A','B'))

        numpy.testing.assert_array_equal(df["A"].vals,
            numpy.array([1,1,2,2,2,3,3,3,4,5,6,6]))

        numpy.testing.assert_array_equal(df["B"].vals,
            numpy.array(["E","F","C","D","F","C","C","D","C","C","A","B"]))

        df = DataFrame(A=A,B=B)

        df = df.sort(('A','B'),reverse=True)

        numpy.testing.assert_array_equal(df["A"].vals,
            numpy.array([6,6,5,4,3,3,3,2,2,2,1,1]))

        numpy.testing.assert_array_equal(df["B"].vals,
            numpy.array(["B","A","C","C","D","C","C","F","D","C","F","E"]))

    def test_filter(self):

        df = DataFrame()

        A = numpy.array([1,1,1,2,2,3,3,3,4,5,6,6,6,6])

        B = numpy.array([
            "A","12text5","text345","125text","C","C","C","C","C","D","E","F","F","F"])

        df["A"] = A
        df["B"] = B

        df = df.filter("B",["E","F"])

        numpy.testing.assert_array_equal(df["A"].vals,
            numpy.array([6,6,6,6]))

        numpy.testing.assert_array_equal(df["B"].vals,
            numpy.array(["E","F","F","F"]))

        df = DataFrame()

        df["A"] = A
        df["B"] = B

        df = df.filter("B",regex=r".*\d")

        numpy.testing.assert_array_equal(df["A"].vals,
            numpy.array([1,1,2]))

        numpy.testing.assert_array_equal(df["B"].vals,
            numpy.array(["12text5","text345","125text"]))

    def test_unique(self):

        df = DataFrame()

        A = numpy.array([1,1,1,2,2,3,3,3,4,5,6,6,6,6])

        B = numpy.array([
            "A","A","B","B","C","C","C","C","C","D","E","F","F","F"])

        df["A"] = A
        df["B"] = B

        df = df.unique(("A","B"))

        numpy.testing.assert_array_equal(df["A"].vals,
            numpy.array([1,1,2,2,3,4,5,6,6]),err_msg="DataFrame.unique() has an issue!")

        numpy.testing.assert_array_equal(df["B"].vals,
            numpy.array(['A','B','B','C','C','C','D','E','F']),err_msg="DataFrame.unique() has an issue!")

        df = df.unique(("A",))

        numpy.testing.assert_array_equal(df["A"].vals,
            numpy.array([1,2,3,4,5,6]),err_msg="DataFrame.unique() has an issue!")

    def test_write(self):

        pass

    def test_writeb(self):

        a = numpy.random.randint(0,100,20)
        b = numpy.random.randint(0,100,20)

        df = DataFrame(a=a,b=b)

class TestDirMaster(unittest.TestCase):

    def test_init(self):

        db = dirmaster()

        db.homedir
        db.filedir

    def test_set_homedir(self):

        db = dirmaster()

        db.set_homedir(__file__)

        db.homedir

    def test_set_filedir(self):

        db = dirmaster()

        db.set_filedir(__file__)

        db.filedir

    def test_get_abspath(self):

        dirmaster().get_abspath(__file__)

    def test_get_dirpath(self):

        dirmaster().get_dirpath(__file__)

    def test_get_fnames(self):

        db = dirmaster()

        db.get_fnames(__file__,returnAbsFlag=True)

class TestHeader(unittest.TestCase):

    def test_init(self):

        names = header(first=['John','Jessica'],last=['Hass','Yummy'])

        self.assertListEqual(names.parameters,['first','last'])
        self.assertListEqual(names.first,['John','Jessica'])
        self.assertListEqual(names.last,['Hass','Yummy'])

        self.assertEqual(names['john'].first,'John')
        self.assertEqual(names['john'].last,'Hass')

        self.assertEqual(names['jessica'].first,'Jessica')
        self.assertEqual(names['jessica'].last,'Yummy')

    def test_all(self):

        df = DataFrame(A=[],B=[])

        front = header(first_name="john",last_name="smith")

        df.child = front

        self.assertEqual(df.child.first_name,["john"])
        self.assertEqual(df.child["john"].first_name,"john")
        self.assertEqual(df.child["john"].last_name,"smith")

        df.gloss = header(mnemonic=[],unit=[],value=[],description=[])

        start = {
            "unit"          : "M",
            "value"         : 2576.,
            "description"   : "it shows the depth logging started",
            "mnemonic"      : "START",
            }
        
        stop = {
            "mnemonic"      : "STOP",
            "unit"          : "M",
            "value"         : 2896.,
            "description"   : "it shows the depth logging stopped",
            }
        
        null = {
            "mnemonic"      : "NULL",
            "value"         : -999.25,
            "description"   : "null values",
            "unit"          : ""
            }

        fld = {
            "mnemonic"      : "FLD",
            "value"         : "FIELD",
            "description"   : "GUNESLI",
            "unit"          : ""
            }

        df.gloss.extend(start)
        df.gloss.extend(stop)
        df.gloss.extend(null)
        df.gloss.extend(fld)

        self.assertListEqual(df.gloss.value,["2576.0","2896.0","-999.25","FIELD"])
        self.assertListEqual(df.gloss.value[1:],["2896.0","-999.25",'FIELD'])

class TestLoad(unittest.TestCase):

    def test_init(self):
        
        txt = "well date oil water gas\n" \
              " A01    1  12    24  36\n" \
              " A01    2  11    23  35\n" \
              " A01    3  10    22  34\n" \
              " A01    4   9    21  33\n" \
              " A01    5   8    20  32\n" \
              " A01    6   7    19  31\n" \
              " A01    7   6    18  30\n" \
              " A01    8   5    17  29\n" \
              " A01    9   4    16  28\n" \
              " A01   10   3    16  27\n" \
              " A01   11   2    14  26\n" \
              " A01   12   1    13  25\n" \
              " B02    1   8    15  25\n" \
              " B02    2   8    15  25\n" \
              " B02    3   8    15  25\n" \
              " B02    4   8    15  25\n" \
              " B02    5   8    15  25\n" \
              " B02    6   8    15  25\n" \
              " B02    7   8    15  25\n" \
              " B02    8   8    15  25\n" \
              " B02    9   8    15  25\n" \
              " B02   10   8    15  25\n" \
              " B02   11   8    15  25\n" \
              " B02   12   8    14  25\n" \

        txtfile = io.StringIO(txt)

        prod = load(txtfile,skiprows=1,headline=0)

        self.assertListEqual(prod.frame["date"].vals[:3].tolist(),[1,2,3.])
        self.assertListEqual(prod.frame.heads,["well","date","oil","water","gas"])
        self.assertListEqual(list(prod.frame.shape),[24,5])

class TestLas(unittest.TestCase):

    def test_init(self):

        pass

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    unittest.main()
