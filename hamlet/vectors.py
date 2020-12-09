from __future__ import print_function    # (at top of module)
import random
import threading
import numpy as np

def getRandVec_int(myLen):
    return np.array([my_random.randint(0, 2, dtype='int') for _ in xrange(myLen)])

def hamming(x, y):
    # This function computes the normalised hamming distance between two binary vectors
    # h = 1.0 - float(np.sum(np.logical_xor(X, Y)))/len(X)
    # count is faster than sum
    return 1.0 - float(np.count_nonzero(np.logical_xor(x, y))) / len(x)

def hammingB(x, y):
    # This function computes the normalised hamming distance between two binary vectors
    # h = 1.0 - float(np.sum(np.logical_xor(X, Y)))/len(X)
    # count is faster than sum
    return 1.0 - float(np.count_nonzero(np.bitwise_xor(x, y))) / len(x)

def hamming_min(X, Y):
    hd_min = 1.0
    for i in xrange(0,n):
        hd = hamming(np.roll(X, -i), Y)
        if hd <= 0.47:
            print(i, hd)
        if hd < hd_min:
            hd_min = hd
    return hd_min


def xorBind(A,B):
    '''
    A xor B is communtative.
    we cyclic shift A by 1 to make this binding non-commutative
    :param A: Vector1 
    :param B: Vector2
    :return:  piA xor B  
    '''
    V = np.logical_xor(np.roll(A, 1), B)*1
    return V

def xorUnBind(A,B):
    V=np.roll(np.logical_xor(A,B),-1)
    return V

def piBind(A,B):
    V= A + np.roll(B,1)
    V = normalize(V[0],2)
    return V

def piUnBind(A):
    V = np.roll(A,-1)
    return V


def createWordVector_GB(word):
    v = symbol_dict[word[0]]
    for a in word[1:]:
        v = xorBind(v, symbol_dict[a])
    return v

def createWordVector_GB_old(word):

    index = symbols.find(word[0])
    V = symbolVector[index]
    wordLength = len(word)

    for i in xrange(1,wordLength):
        index = symbols.find(word[i])
        V = xorBind(V,symbolVector[index])

    return V

# ----------------------------------------------------------------------


def XOR_I(v1, v2):
    try:
        return np.logical_xor(v1, v2) * 1
    except AttributeError:
        v1=v1

def addVecMajority_int(vecList, shift, Rv=None):
    return normalizeVector_int(addVecMajority(vecList, shift), len(vecList), Rv)

def normalizeVector_int(sv, seqlength, Rv=None):
    v = sv.copy() # we don't want to change sv
    if seqlength % 2 == 0:
        if Rv is None:
            v = v + getRandVec(len(v))
        else:
            v = v + Rv
        seqlength += 1

    v[v < float(seqlength / 2.0)] = 0  # using cast because of running in python 2.7
    v[v > float(seqlength / 2.0)] = 1

    return v

def addVecMajority_intRAW(vecList, shift):
    sumVec = np.zeros(len(vecList[0]), dtype='int')
    pwr = 0
    for bva in vecList:
        bvshift = bva[:]
        if shift >= 0:
            bvshift = np.roll(bvshift, pwr)
            pwr += shift
        sumVec += bvshift
    return sumVec

def addVecMajority_intPerm(vecList, perm=None):
    sumVec = np.zeros(len(vecList[0]), dtype='int')
    pwr = 0
    if perm is not None:
        shift = True
    else:
        shift = False
    for bva in vecList:
        bvshift = bva[:]
        if shift:
            bvshift = xor(bva, perm)
            perm = np.roll(perm, 1)
        sumVec += bvshift
    return sumVec

def addVecMajority_intPerm1(vecList, perm=None):
    sumVec = np.zeros(len(vecList[0]), dtype='int')
    pwr = 0
    if perm is not None:
        shift = True
    else:
        shift = False
    for bva in vecList:
        bvshift = bva[:]
        if shift:
            bvshift = np.roll(bvshift, pwr)
            bvshift = xor(bvshift, perm)
            pwr += 1
        sumVec += bvshift
    return sumVec

def addVecMajority_intPerm2(vecList, perm=None):
    sumVec = np.zeros(len(vecList[0]), dtype='int')
    pwr = 0
    if perm is not None:
        shift = True
    else:
        shift = False
    for bva in vecList:
        if shift:
            bvshift = xor(bva, perm[pwr])
            pwr += 1
            sumVec += bvshift
        else:
            sumVec += bva

    return sumVec

def showMatches1(veclist, a, expected):
    bestMatch = float('-inf')
    n = 0
    for v in veclist:
        match = hamming(v, a)
        if match >= 0.53 and n != expected:
            print("HD_", n, ' <->', n, "{:0.4f}".format(match))
        if match > bestMatch:
            bestMatch = match
            vecname = n
        n += 1
    return vecname, bestMatch


def create_base_vecs(start, end, veclen, ascii_names=True):
    base_vecs = {}  # Dictionary(Of String, BitArray)
    if ascii_names:
        start = ord(start)
        end = ord(end)
    for x in range(start, end + 1):  # inclusive of end
        if ascii_names:
            c = chr(x)
        else:
            c = x
        base_vecs.update({c: getRandVec(veclen)})
        base_vecs.items()

    return base_vecs


def get_number(invec):
    for k, v in num_dict.items():
        hd = hamming(invec, v)
        if hd > 0.54:
            return k

    return ""


def make_number_vec(val_str):
    num_vec = num_dict[val_str[0]]
    cnt = 0
    for d in val_str[1:]:
        cnt += 1
        num_vec = num_vec + ROLL(num_dict[d], cnt)

    return normalize(num_vec, cnt+1)


def decode_numbervec(numvec):
    match = ""
    l = "a"
    while l != "":
        l = get_number(numvec)
        match += l
        numvec = ROLL(numvec, -1)

    return match


class NewChunkPvecs(object):
    mythreadlock = threading.Lock()
    next_chunk_id = 0
    break_on_chunk_id = -1
    myrandom = None
    trace_threshold = 0.53 # 0.525  # 0.54  # 0.532
    maxchunksize = 51
    repeat_stop = 0
    padsize = maxchunksize + (repeat_stop + 1) + 1
    maxvecs = 20
    maxrandoms = 50
    levelvecs = []
    permVecs = None
    padvecs = None
    role_posn = None  # POSITION-Role-vector
    role_payload = None  # POSITION-Role-vector
    role_data = None  # DATA-Role-vector
    role_match_message = None  # Used to collect matches on services
    role_id = None  # Used to id messages
    role_matchval = None  # Used to decode match values
    role_stopvec = None  # Used to decode match values

    def __init__(self, name, veclist, level, payload=None, maxvecs=60, chunks=None, do_not_pad=True):
        self.name = name
        self.level = level
        self.chunksize = len(veclist)
        self.veclen = len(veclist[0])

        # Initialise the class variables if not done
        NewChunkPvecs.maxvecs = maxvecs
        if NewChunkPvecs.myrandom is None:
            self.init_class_vars(self.veclen)

        self.chunk_id = NewChunkPvecs.next_chunk_id
        with NewChunkPvecs.mythreadlock:
            NewChunkPvecs.next_chunk_id += 1

        self.veclist = veclist[:]  # the real vectors, for debug and possible use in clean up
        self.chunklist = chunks  # the real vectors, for debug and possible use in clean up
        #self.stopvec = NewChunkPvecs.role_stopvec  # self.getRandVec(self.veclen)
        self.stopvec = self.getRandVec(self.veclen)
        self.start_tag_vec = None

        self.veclist.append(self.stopvec)
        #vlist.append(NewChunkPvecs.levelvecs[level])

        # create the compond vector and store it
        # self.myvec = XOR(NewChunkPvecs.levelvecs[level], self.addvecs(self.veclist))

        self.pad_count = 0  # For DEBUG
        self.myvec_raw = None
        self.raw_cnt = 0
        self.__myvec = None
        self.myvec = self.addvecs(self.veclist, do_not_pad=do_not_pad)

        # dmy = self.getPermutorDEBUG(self.myvec, self.veclist[0])
        #if self.level == 2:
        #    self.recoverAllPermutorsDebug(self.myvec)

        self.next_vec = None
        self.commandvec = None


    @property
    def myvec(self):
        return np.unpackbits(self.__myvec)

    @myvec.setter
    def myvec(self, myvec):
        self.__myvec = np.packbits(myvec)


    @staticmethod
    def init_class_vars(veclen):
        # One time initialisation of permutation vectors
        NewChunkPvecs.next_chunk_id = 0
        NewChunkPvecs.myrandom = [1]  # using global numpy myrand ATM  # np.random.RandomState(123)
        NewChunkPvecs.padvecs = [NewChunkPvecs.getRandVec(veclen) for _ in xrange(NewChunkPvecs.maxrandoms)]
        NewChunkPvecs.levelvecs = [NewChunkPvecs.getRandVec(veclen) for _ in xrange(5)]
        NewChunkPvecs.role_posn = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.role_data = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.role_match_message = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.role_id = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.role_matchval = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.role_stopvec = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.permVecs = []
        for _ in xrange(2):
            NewChunkPvecs.permVecs.append([NewChunkPvecs.getRandVec(veclen) for _ in xrange(NewChunkPvecs.padsize+150)])

    @classmethod
    def createchunkfromvecs(cls, name, veclist, level, payload=None, maxvecs=60):
        return cls(name, veclist, level, payload, maxvecs)

    @classmethod
    def createchunkfromchunks(cls, name, chunks, level, payload=None, maxvecs=60):
        veclist = [c.myvec for c in chunks]
        return cls(name, veclist, level, payload, maxvecs, chunks)

    @classmethod
    def buildchunks(cls, name, chunklist, level, payload=None):
        """
        
        :param name: Name of this chunk
        :param chunksize: Max entries in a single chunk
        :param level: hiearchy_level intentional side effect modifies level in outside world 
        :param payload: perhaps for tuture binding of data
        :return: top level chunk of a heirachy built from the flat list of chunks supplied 
        """
        m = 0
        llen = len(chunklist)
        if llen > cls.maxchunksize:
            while m + cls.maxchunksize <= llen:
                level[0] += 1  # sub chunks were at one level higher than their children
                m = 0
                chnks = []
                cnt = 0
                while m + cls.maxchunksize < llen:
                    # when the remaining list is less than two chunks we want to split it equally
                    if llen - m < cls.maxchunksize * 2:
                        break
                    sub_chunk_list = chunklist[m:m + cls.maxchunksize]
                    chnks.append(cls.createchunkfromchunks(name + '_part' + str(cnt), sub_chunk_list, level[0]))
                    m += cls.maxchunksize
                    cnt += 1

                if m < llen:  # we want to split the remainder into two fairly even chunks
                    msplit = int((llen - m) / 2)
                    chnks.append(cls.createchunkfromchunks(name + '_part' + str(cnt), chunklist[m:m+msplit], level[0]))
                    m += msplit
                    cnt += 1
                    chnks.append(cls.createchunkfromchunks(name + '_part' + str(cnt), chunklist[m:llen], level[0]))

                if len(chnks) <= cls.maxchunksize:
                    chunklist = chnks
                    break
                else:
                    chunklist = chnks[:]

        level[0] += 1  # sub chunks were built so final chunk is at one level higher than its children
        dbcnks = cls.createchunkfromchunks(name, chunklist, level[0])
        return dbcnks
        # return NewChunkPvecs.createchunkfromchunks(name, chunklist, level)

    def get_start_vec(self):
        #sumv = normalize(self.myvec_raw + NewChunkPvecs.role_posn + self.stopvec, self.raw_cnt + 2)
        sumv = normalize(self.myvec_raw + NewChunkPvecs.role_posn, self.raw_cnt + 1)
        return ROLL(XOR(NewChunkPvecs.permVecs[0][0], sumv), -1)

    def check_for_activation(self, invec, myvec):

        match = hamming(invec, myvec)
        if match < NewChunkPvecs.trace_threshold:
            return match, invec
        else:
            return match, self.new_get_next_vector(invec)

    def new_get_next_vector(self, invec):

        pindex = 0
        #try:
        pvec = NewChunkPvecs.role_posn
        for p in NewChunkPvecs.permVecs[0]:
            pvec = ROLL(XOR(pvec, ROLL(p, pindex)), -1)
            hd = hamming(pvec, invec)
            if hd >= NewChunkPvecs.trace_threshold:
                # We know if we are better than threshold that we have the best match on role_posnfinder
                # because only one pvec.role_posnfinder combo will ever be a match
                break
            pindex -= 1

        # Calculate the next transmission vector from the found pindex
        pindex -= 1
        pvec = ROLL(NewChunkPvecs.permVecs[0][0 - pindex], pindex)
        nextvec = ROLL(XOR(pvec, invec), -1)
        #except IndexError:
        #    pindex=pindex

        return nextvec

    def check_for_activation_faster_safe(self, invec, myvec):
        match = 0
        pindex = 0
        for p in NewChunkPvecs.permVecs[0]:
            pvec = ROLL(p, pindex)
            nextvec = ROLL(XOR(pvec, invec), -1)
            match = hamming(nextvec, myvec)
            if match > NewChunkPvecs.trace_threshold:
                # We know of we are better than threshold that we have the best match
                # for self.myvec because we can not match the current invec in more than one combination
                return match, nextvec
            pindex -= 1

        # if we get to here we have failed to find a valid match
        return match, -1

    def check_for_activation_safe(self, invec, myvec):
        bestmatch = 0
        best_nextvec = None
        bestidx = 0
        for pindex in xrange(len(NewChunkPvecs.permVecs[0])):
            pvec = ROLL(NewChunkPvecs.permVecs[0][pindex], -1 * pindex)
            nextvec = ROLL(XOR(pvec, invec), -1)
            match = hamming(nextvec, myvec)
            if match > bestmatch:
                bestmatch = match
                bestidx = pindex
                best_nextvec = nextvec

        if bestmatch > NewChunkPvecs.trace_threshold:  # For DEBUG
            bestmatch = bestmatch
        if bestmatch < NewChunkPvecs.trace_threshold:
            return bestmatch, -1
        else:
            return bestmatch, best_nextvec

    def get_next_vector(self):
        pvec = ROLL(NewChunkPvecs[0][self.next_vec + 1], -1 * self.next_vec)
        nextvec = ROLL(XOR(pvec, self.commandvec), -1)
        return nextvec

    def check_for_stopvec(self, invec, myvec):
        return self.check_for_activation(invec, myvec)

    def addvecs(self, veclist, mypayload=None, do_not_pad=False):
        # Adding like this, a + (p0 * b) + (p0 * p1 * c) + .... note: 'p' vectors are random but the same for all chunks
        # Using this method we gain benefit because we will get better similarity matchups
        # since sequence is controlled by a fixed set of random vectors
        # sumvec = self.prep_payload(veclist[0], 1, mypayload)

        #try:
        sumvec = NewChunkPvecs.role_posn
        pindex = 0
        piv = NewChunkPvecs.permVecs[0][0]
        sumvec = XOR(piv, ROLL(veclist[0], pindex + 1))
        cnt = 1
        v = sumvec   # so that scope of v persists after loop
        for y in veclist[1:]:
            cnt += 1
            pindex += 1
            piv = XOR(piv, NewChunkPvecs.permVecs[0][pindex])
            v = XOR(piv, ROLL(y, pindex + 1))
            sumvec = sumvec + v
        #except IndexError:
        #    pindex=pindex


        # pre_start_stop_vec = normalize(sumvec, cnt)

        # self.start_tag_vec = XOR(NewChunkPvecs.role_posn, pre_start_stop_vec)
        #self.stopvec = XOR(NewChunkPvecs.role_stopvec, pre_start_stop_vec)

        #pindex += 1
        #piv = XOR(piv, NewChunkPvecs.permVecs[0][pindex])
        #self.stopvec = XOR(piv, ROLL(self.stopvec, pindex + 1))


        # We can add multiple copies of the the stop vec to cause its match to improve
        # Using the exact same 'v' will improve matches for the stopvec
        for _ in xrange(NewChunkPvecs.repeat_stop):
            cnt += 1
            sumvec = sumvec + v

        if not do_not_pad:
            self.pad_count = 0  # For DEBUG
            while cnt < NewChunkPvecs.padsize:
                cnt += 1
                self.pad_count += 1
                sumvec = sumvec + self.makerandom()

        self.myvec_raw = sumvec
        self.raw_cnt = cnt
        nv = normalize(sumvec, cnt)

        # Debug
        #
        #if max(nv) > 1:
        #    print("oops")
        #hd_stopvec_check = hamming(nv, v)
        #if hd_stopvec_check < 0.532:  # or hd_stopvec_check >= 0.6:
        #    print("Stopvec_check:", hamming(nv, v), self.name)

        return nv

    def prep_payload(self, sv, p, mydata):
        # We keep each compoment separate so that we have a three way sum
        pvec_payload = XOR(
            NewChunkPvecs.numvecs[p],
            XOR(NewChunkPvecs.role_posn, NewChunkPvecs.permVecs[0][p]))  # next Pvec in the sequence

        data_vec = XOR(ROLL(sv, 1), XOR(NewChunkPvecs.role_data,
                                        self.makerandom()))  # For Debug Custome payload

        return pvec_payload, data_vec

    def prep_payload_0(self, sv, p, mydata):
        # We keep each compoment separate so that we have a three way sum
        pvec_payload = XOR(ROLL(sv, 1), XOR(NewChunkPvecs.role_posn,
                                            NewChunkPvecs.permVecs[0][p]))  # next Pvec in the sequence
        data_vec = XOR(ROLL(sv, 1), XOR(NewChunkPvecs.role_data,
                                        self.makerandom()))  # For Debug Custome payload

        return pvec_payload, data_vec
        #return normalize(pvec_payload + data_vec, 2)
        #sumvec = sv + normalize(pvec_payload + data_vec, 2)
        #svn = normalize(sumvec, 2)
        #return svn

    def prep_payload_1(self, sv, p, mydata):
        # We keep each compoment separate so that we have a three way sum
        pvec_payload = XOR(NewChunkPvecs.role_posn, NewChunkPvecs.permVecs[0][p])  # next Pvec in the sequence
        data_vec = XOR(NewChunkPvecs.role_data, self.makerandom())  # For Debug Custome payload
        return XOR(ROLL(sv, 1), normalize(pvec_payload + data_vec, 2))

    def prep_payload_2(self, sv, p, mydata):
        # We keep each compoment separate so that we have a three way sum
        pvec_payload = XOR(ROLL(sv, 1),
                           XOR(NewChunkPvecs.role_posn, NewChunkPvecs.permVecs[0][p]))  # next Pvec in the sequence
        data_vec = XOR(ROLL(sv, 1),
                       XOR(NewChunkPvecs.role_data, self.makerandom()))  # For Debug Custome payload
        newv = normalize(sv + pvec_payload + data_vec, 3)
        return newv

    def makerandom(self):
        # We can probably get speed up by using a large pool of class RandomVecs which would only be generated once
        # And possibly a smaller set of class Randoms by utilising shifts and xors
        # We can use a small fixed set of Randoms because this will breed incorrect similarities
        r1 = my_random.randint(0, NewChunkPvecs.maxrandoms, dtype='int')
        r2 = my_random.randint(0, self.veclen, dtype='int')
        r3 = my_random.randint(0, NewChunkPvecs.maxrandoms, dtype='int')
        r4 = my_random.randint(0, self.veclen, dtype='int')
        return XOR(np.roll(NewChunkPvecs.padvecs[r1], r2), np.roll(NewChunkPvecs.padvecs[r3], r4))

    def flattenchunkheirachy(self, allchunks):
        if self.chunklist is None:
            allchunks.append(self)
            return
        else:
            allchunks.append(self)
            for c in self.chunklist:
                c.flattenchunkheirachy(allchunks)

    def get_flat_list_of_vectors_from_chunkheirachy(self, all_vecs):
        # We only want vectors that represent services
        # So we are picking each self.myvec entry from every chunk
        if self.chunklist is None:
            all_vecs.append(self.myvec)
            return
        else:
            all_vecs.append(self.myvec)
            for c in self.chunklist:
                c.get_flat_list_of_vectors_from_chunkheirachy(all_vecs)

    @staticmethod
    def getRandVec(mylen):
        # return np.array([NewChunkPvecs.myrandom.randint(0, 2, dtype='int') for _ in xrange(mylen)])
        return np.array([my_random.randint(0, 2, dtype='int') for _ in xrange(mylen)])

    def verifychunkstructure(
            self, invec, minmatch, maxmatch, minstop, maxstop, errors, linenumber, rpt_lines=2, rpt_stops=2):

        vtab = "\t" * (5 - self.level)  # Format contol
        linenumber[0] += 1
        # First match myself
        if invec is None:
            match = 1.0  # This is the start of recursion
            next_vec = None
        else:
            match, next_vec = self.check_for_activation(invec, self.myvec)
        if match < minmatch[0]:
            minmatch[0] = match
        if match != 1.0 and match > maxmatch[0]:
            maxmatch[0] = match
        passed = False
        if match > NewChunkPvecs.trace_threshold:
            if rpt_lines == 2:
                print ("Verified: {:04d}, {:05.4f}{:s}{:s}".format(linenumber[0], match, vtab, self.name))
            passed = True
        else:
            passed = False
            errors.append("FAILED: {:04d}, {:0.4f}{:s}{:s},".format(linenumber[0], match,vtab,self.name))
            if rpt_lines >= 1:
                print("\t\t\t", linenumber[0], "FAILED:", match, vtab,  self.name)

        if self.level == 0:
            # Here we should verify the stop vector
            # return 'STOP', passed, XOR(self.getPermutor(invec), invec)
            return 'STOP', passed, next_vec

        # Then, pass or fail, loop thro my subchunks recursively
        # startvec = self.myvec
        startvec = ROLL(XOR(NewChunkPvecs.permVecs[0][0], self.myvec), -1)
        cnt = 0
        failedStopVector = False
        for c in self.chunklist:
            gotstop, passed, startvec = c.verifychunkstructure(
                startvec, minmatch, maxmatch, minstop, maxstop, errors, linenumber, rpt_lines, rpt_stops)

            if cnt == self.chunksize-1:
                stopmatch, dmy = self.check_for_activation(startvec, self.stopvec)
                if stopmatch < minstop[0]:
                    minstop[0] = stopmatch
                if stopmatch != 1.0 and stopmatch > maxstop[0]:
                    maxstop[0] = stopmatch
                if stopmatch > NewChunkPvecs.trace_threshold:
                    if rpt_stops == 2:
                        print("Verified: {:04d}, {:05.4f}\t\tSTOP-VEC".format(linenumber[0], match))
                else:
                    passed = False
                    failedStopVector = True
                    errors.append("FAILED: {:d}, {:0.4f}{:s}{:s},".format(linenumber[0], match, vtab, "\t\tSTOP-VEC"))
                    if rpt_stops >= 1:
                        print("\t\t\t", linenumber[0], "FAILED:", match, "\t\tSTOP-VEC")

            cnt += 1

        return 'STOP', passed, next_vec

    def searchvec(self, chunkvecs):
        failed = False
        failedPosns = []
        #v6 = XOR(NewChunkPvecs.levelvecs[self.level], self.myvec)
        v6 = self.myvec
        for pindex in xrange(1, self.chunksize+1):
            name, bestmatch = showMatches1(chunkvecs, v6, pindex)
            v6 = XOR(v6, NewChunkPvecs.permVecs[0][pindex])
            print("Best-HD_", pindex, ' <->', name, "{:0.4f}".format(bestmatch))

            if name + 1 != pindex:
                failedPosns.append(pindex)
                failed = True
        if failed:
            print("failed", failedPosns)
        else:
            print("passed, vecLen:", len(chunkvecs[0]))

    def getbestchunk(self, chunklist, tracevec):
        bestMatch = float('-inf')
        #myvec = XOR(NewChunkPvecs.levelvecs[self.level], tracevec)
        myvec = tracevec
        stopmatch = hamming(myvec, self.stopvec)
        if stopmatch > 0.53:
            return None, "stop", stopmatch

        for c in chunklist:
            match = hamming(c.myvec, myvec)
            if match == 1:
                continue  # We need to skip past ourself
            # if match >= 0.53:
            #    print("HD  <->", c.name, "{:0.4f}".format(match))
            if match > bestMatch:
                bestMatch = match
                bestchunk = c

        return bestchunk, bestchunk.name, bestMatch

    def recurse_chuncktree(self, allchunks, vtabs):
        if self.level == 2:
            print(vtabs, "Do my work:", self.name)
            return
        # print("Entering chunk,", chunk.name, chunk.level)
        tracevec = self.myvec
        for pindex in xrange(NewChunkPvecs.maxvecs):
            bestchunk, name, bestmatch = self.getbestchunk(allchunks, tracevec)
            print(vtabs, name, "HD = ", bestmatch)
            if name == "stop":
                return
            else:
                bestchunk.recurse_chuncktree(allchunks, vtabs + "\t")

            # Service then does its 'shift' and retransmits to start the next pier
            tracevec = XOR(tracevec, bestchunk.getPermutor(pindex))
            # however before it does the transmit it checks for a stopvec
            # we can do this here because the best match should alsways be the stopvec if
            # the stopvec is next in line since stopvec is a random atomic vec and should not
            # be similar to anything else
            stopmatch = hamming(tracevec, self.stopvec)
            if stopmatch > 0.53:
                print("Stop HD = ", bestmatch)
                return None, "stop", stopmatch

        return


class NewChunk(NewChunkPvecs):
    # -----------------------
    # 138 runs no errors with
    # trace_threshold = 0.532
    # maxchunksize = 51
    # padsize = 51  # 69
    # repeat_stop = 1
    # maxvecs = 100
    # maxrandoms = 50
    # -----------------------

    #trace_threshold = 0.54
    #maxchunksize = 31
    #padsize = 31  # 69
    #repeat_stop = 2
    #maxvecs = 100
    #maxrandoms = 50

    trace_threshold = 0.532
    maxchunksize = 51
    repeat_stop = 1
    padsize = maxchunksize + (repeat_stop + 1)  # 1st stop is added to end of list, repeat_stop allows stren
    maxvecs = 100
    maxrandoms = 50

    def __init__(self, name, veclist, level, payload=None, maxvecs=100, chunks=None):
        super(NewChunk, self).__init__(name, veclist, level, payload, maxvecs, chunks)

    @staticmethod
    def init_class_vars(veclen):
        # One time initialisation of permutation vectors
        NewChunkPvecs.myrandom = 1 # np.random.RandomState(123)
        NewChunkPvecs.padvecs = [NewChunk.getRandVec(veclen) for _ in xrange(NewChunkPvecs.maxrandoms)]
        NewChunkPvecs.levelvecs = [NewChunk.getRandVec(veclen) for _ in xrange(5)]
        NewChunkPvecs.role_posn = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.role_data = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.role_match_message = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.role_id = NewChunkPvecs.getRandVec(veclen)
        NewChunkPvecs.role_matchval = NewChunkPvecs.getRandVec(veclen)
        # not using permVecs

    def get_start_vec(self):
        return self.myvec

    def check_for_activation(self, invec, myvec):
        """
        There are TWO return values
        :param invec: 
        :param myvec: 
        :return: Hamming distance between vecs,  position_control_vec 
        """
        return hamming(invec, myvec), ROLL(myvec, 1)

    def check_for_stopvec(self, invec, myvec):
        """
        There are TWO return values
        :param invec: 
        :param myvec: 
        :return: Hamming distance between vecs,  position_control_vec 
        """
        return hamming(invec, myvec), ROLL(self.myvec, 1)

    def addvecs(self, veclist):
        # This is used to drive the non-match to below 0.53
        # There maybe a quicker cheat for this, during normalisation addin more randomvectors
        # this will stop us having to do extra XOR's
        # Bind like this, a + pia * b + pia * pib * c....  (note each vector is shifted only once i.e. not pi_squared(b)

        if len(veclist) > NewChunk.maxchunksize + 1:
            print("what happened")
        sumvec = veclist[0]
        piv = np.roll(sumvec, 1)
        v = sumvec  # scope of v need to be external to the loop
        cnt = 1
        for y in veclist[1:]:
            v = XOR(piv, y)
            sumvec = sumvec + v
            piv = XOR(piv, np.roll(y, 1))
            cnt += 1

        # We add multiple copies of the the stop vec to cause its match to improve
        # Using the exact same 'v' will improve matches for the stopvec
        for _ in xrange(NewChunkPvecs.repeat_stop):
            cnt += 1
            sumvec = sumvec + v

        self.pad_count = 0  # For DEBUG
        while cnt < NewChunkPvecs.padsize:
            cnt += 1
            self.pad_count += 1
            sumvec = sumvec + self.makerandom()

        #if NewChunk.padsize - NewChunkPvecs.repeat_stop - self.chunksize < 0:
        #    nv = normalize(sumvec, len(veclist) + NewChunkPvecs.repeat_stop)
        #else:
        #    nv = normalize(sumvec, NewChunk.padsize)
        nv = normalize(sumvec, cnt)
        if max(nv) > 1:
            print("oops")

        hd_stopvec_check = hamming(nv, v)
        if hd_stopvec_check < 0.532:  # or hd_stopvec_check >= 0.6:
            print("Stopvec_check:", hamming(nv, v), self.name)
        return nv

    def searchvec(self, chunkvecs):
        failed = False
        failedPosns = []
        v6 = self.myvec
        for i in xrange(self.chunksize):
            name, bestmatch = showMatches1(chunkvecs, v6, i)
            v6 = XOR(v6, np.roll(chunkvecs[i], 1))
            print("Best-HD_", i, ' <->', name, "{:0.4f}".format(bestmatch))
            if name != i:
                failedPosns.append(i)
                failed = True
        if failed:
            print("failed", failedPosns)
        else:
            print("passed, vecLen:", len(chunkvecs[0]))

    def getPermutor(self, pindex):
        return np.roll(self.myvec, 1)


def createSymbolVectors_GB(symbols, veclen):

    # Create an array of symbol vectors for each symbol in the dictionary using one of the random number vectors as a seed

    sym = np.array([my_random.randint(0, 2, dtype='int') for _ in xrange(veclen)])
    SYM = [sym]
    for i in xrange(1, len(symbols)):
        sym = np.array([my_random.randint(0, 2, dtype='int') for _ in xrange(veclen)])
        SYM = SYM + [sym]
    return SYM

def createSymbolVectors(symbols, veclen):
    # A dictionary is slightly faster than Graham's list look up but only marginally....
    sym = {}

    for a in symbols:
        sym[a] = np.array([my_random.randint(0, 2, dtype='int') for _ in xrange(veclen)])

    return sym

xor = XOR_I
#addVecMajority = addVecMajority_intPerm
addVecMajority = addVecMajority_intPerm2
getRandVec = getRandVec_int
createWordVector = createWordVector_GB

# HD = HD_int   #Numpy binary vectors (1,0) integers

# HD = lambda v1,v2: np.sum(np.logical_xor(v1,v2))  # This is slower than count
HD = lambda v1, v2: 1 - np.count_nonzero(np.logical_xor(v1, v2))/len(v1)
XOR = XOR_I  # this is numpy logical_XOR
invX = XOR_I  # XOR is its own inverse
ROLL = lambda v, shift: np.roll(v, shift)
# roll = lambda v, shift: v
addVecMajority = addVecMajority_int
normalize = normalizeVector_int

my_random = np.random.RandomState(0)
symbols = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890.;:,_'!?-[]&*"

symbolVector = None  # changed to symbol_dict # createSymbolVectors(symbols, 10000)
symbol_dict = createSymbolVectors(symbols, 10000)
num_dict = create_base_vecs("0", "9", 10000, True)



