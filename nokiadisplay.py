from peripheral import peripheral, TrueValues, FalseValues
import hx1230_fb
from machine import Pin, SPI


def show(s, text, col=None, row=None):
    # col = argk["col"] if "col" in argk else None
    if col != None:
        if col.__class__ is str and col.isdigit():
            pass
        else:
            col = True if col in TrueValues else False

    if row != None:
        if row.__class__ is str and row.isdigit():
            pass
        else:
            row = True if row in TrueValues else False

    return s.show(text, col, row)


def clearRow(s, row, color=0):
    return s.clearRow(row)


def clearCol(s, col, color=0):
    return s.clearCol(col)


def clearChar(s, col, row, color=0):
    return s.clearChar(col, row, color)


def clear(s):
    s.lcd.clear()
    return {"clear": "done"}


def resetCursor(s, rows=True, cols=True):
    if rows in TrueValues:
        s.setRowIterator()
    if cols in TrueValues:
        s.setColIterator()
    return {"cursor": "resetdone"}


class nokiadisplay(peripheral):
    def __init__(self, options={"pinOut": 5}):
        super().__init__(options)

        spi = SPI(2, baudrate=2000000, polarity=0, phase=0, bits=8,
                  firstbit=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
        cs = Pin(5)
        rst = Pin(16)

        self.pType = self.__class__.__name__
        self.pClass = "OUT"

        self.commands["show"] = show
        self.commands["clear"] = clear
        self.commands["clearCol"] = clearCol
        self.commands["clearRow"] = clearRow
        self.commands["clearChar"] = clearChar
        self.commands["resetCursor"] = resetCursor

        self.lcd = hx1230_fb.HX1230_FB_SPI(spi, cs, rst)

        self._row = 0
        self._col = 0
        self.setRowIterator()
        self.setColIterator()

        self.lcd.clear()

    def setRowIterator(self, startFrom=0):
        self.availableRows = int(self.lcd.height/8)+1
        self.rowsRange = range(startFrom, self.availableRows-1)
        self.rowsIter = iter(self.rowsRange)

    def setColIterator(self, startFrom=0):
        self.availableCols = int(self.lcd.width/8)+1
        self.colsRange = range(startFrom, self.availableCols-1)
        self.colsIter = iter(self.colsRange)

    def linePixel(self, n):
        return 8*n

    def clearRow(self, row, color=0):
        lineN = int(row)

        y = self.linePixel(lineN)
        x = 0
        yt = self.linePixel(1)
        xt = self.linePixel(self.availableCols)

        self.lcd.fill_rect(x, y, xt, yt, color)
        self.lcd.show()

        return {
            "clearRow": "done",
            "x": x,
            "y": y,
            "xt": xt,
            "yt": yt,
            "row": row
        }

    def clearCol(self, col, color=0):
        colN = int(col)

        x = self.linePixel(colN)
        y = 0
        xt = self.linePixel(1)
        yt = self.linePixel(self.availableRows)

        self.lcd.fill_rect(x, y, xt, yt, color)
        self.lcd.show()
        return {
            "clearCol": "done",
            "x": x,
            "y": y,
            "xt": xt,
            "yt": yt,
            "col": col
        }

    def clearChar(self, col, row, color=0):
        coln = int(col)
        rown = int(row)

        x = self.linePixel(coln)
        y = self.linePixel(rown)
        xt = self.linePixel(1)
        yt = self.linePixel(1)

        self.lcd.fill_rect(x, y, xt, yt, color)
        self.lcd.show()
        return {
            "clearChar": "done",
            "x": x,
            "y": y,
            "xt": xt,
            "yt": yt,
            "col": col,
            "row": row
        }

    @peripheral._trigger
    def show(self, text, col=None, row=None):
        # col=True sau row = True tine valoare curenta, nu trece prin iter

        if col.__class__.__name__ == "NoneType":
            col = self.col
        else:
            if col.__class__ is bool and col == True:
                col = self._col
            else:
                col = self.linePixel(int(col))

        if row.__class__.__name__ == "NoneType":
            row = self.row
        else:
            if row.__class__ is bool and row == True:
                row = self._row
            else:
                row = self.linePixel(int(row))

        self.lcd.text(text, col, row)
        self.lcd.show()

        return {"col": int(col/self.linePixel(1)), "row": int(row/self.linePixel(1)), "text": text}

    @property
    def row(self):
        try:
            self._row = next(self.rowsIter)
        except StopIteration:
            self.rowsIter = iter(self.rowsRange)
            self._row = next(self.rowsIter)

        return self.linePixel(self._row)

    @row.setter
    def row(self, val):
        if int(val) < self.availableRows:
            self.setRowIterator(int(val))
            self._row = next(self.rowsRange)

    @property
    def col(self):
        try:
            self._col = next(self.colsIter)
        except StopIteration:
            self.colsIter = iter(self.colsRange)
            self._col = next(self.colsIter)

        return self.linePixel(self._col)

    @col.setter
    def col(self, val):
        if int(val) < self.availableCols:
            self.setColIterator(int(val))
            self._col = next(self.colsRange)

    def getState(self):
        return {"row": self._row, "col": self._col}

    def getObservableMethods(self):
        return ["show"]

    def getObservableProperties(self):
        return []
