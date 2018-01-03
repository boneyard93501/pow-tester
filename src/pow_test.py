#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
    simple proof of work with rudimentary runtime stats
    to test a few different *nixes, e.g., rasbian, os x,
    ubuntu, alpine, and hardware instances, e.g., pi, ec2,
    mac.

    12/29/2017
'''
import os,sys
import datetime
from struct import calcsize
from statistics import mean, median, stdev

if calcsize('P') * 8 == 64:
    from hashlib import blake2b as blake2
else:
    from hashlib import blake2s as blake2


def proof_of_work(difficulty,data,digest_size=32):
    '''
        ever so simplistic
        : difficulty    number of leading zeros
        : data          some string of stuff, e.g. block header

        return hash, nonce, iterations
    '''
    if not isinstance(data,str):
        data = '{}'.format(data)

    index = 1
    new_hash = None
    nonce = None
    while 1:
        n_seed = bytes('{}'.format(index),'utf8')
        nonce = blake2(n_seed,digest_size=8).hexdigest()
        __ = bytes(data + '{}'.format(nonce),'utf8')
        h = blake2(__,digest_size=digest_size)

        if h.hexdigest()[:difficulty] == "0" * difficulty:
            new_hash = h.hexdigest()
            break
        index += 1

    return new_hash, nonce, index


def test_pow(difficulty=4,result_variance=False):
    '''
    '''
    start_dt = datetime.datetime.utcnow()
    last_hash = 'Howdy'
    last_height = 10
    data = last_hash + str(last_height)
    if result_variance:
        data += start_dt.isoformat()

    h,n,i = proof_of_work(difficulty,data)
    end_dt = datetime.datetime.utcnow()

    v = blake2(bytes(data + n,'utf8'),digest_size=32).hexdigest()
    _assert = v==h

    vals = (difficulty,(end_dt - start_dt).total_seconds(),i,h,n,v,_assert)
    msg = 'pow test run with verification assert:\n'
    msg += 'difficulty: {}, run time: {}, iterations: {}\n'
    msg +='pow hash: {}, pow nonce: {},verification hash: {}\n'
    msg +='pow == verification hash: {}'
    sys.stdout.write(msg.format(*vals))

    return _assert


def pow_performance_check(difficulties,max_rounds):
    '''
        thredaing isn't really the answer. i want the processing times as
        pure as possible ont eh respective platforms and the ec2 t instances
        are choking enough with one run as is.
    '''
    local_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    log_dir = os.path.abspath(os.path.join(local_dir,'..','logs'))
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    fake_data = blake2(bytes(datetime.datetime.utcnow().isoformat(),'utf8'),digest_size=32).hexdigest()

    result = {}
    for d in difficulties:
        result[d] = {}
        __ = {'td':[],'n':[]}
        for m in range(max_rounds):
            start_dt = datetime.datetime.now()
            h,n,i = proof_of_work(d,fake_data)
            fake_data = h + n
            end_dt = datetime.datetime.now()

            __['td'].append((end_dt - start_dt).total_seconds())
            __['n'].append(i)

        result[d]['rounds'] = max_rounds
        result[d]['run-time'] = {}
        result[d]['hash-iters'] = {}
        result[d]['run-time']['avg'] = round(mean(__['td']),4)
        result[d]['run-time']['median'] = round(median(__['td']),4)
        result[d]['run-time']['stdev'] = round(stdev(__['td']),4)
        result[d]['run-time']['min'] = round(min(__['td']),4)
        result[d]['run-time']['max'] = round(max(__['td']),4)

        result[d]['hash-iters']['avg'] = round(mean(__['n']),4)
        result[d]['hash-iters']['median'] = round(median(__['n']),4)
        result[d]['hash-iters']['stdev'] = round(stdev(__['n']),4)
        result[d]['hash-iters']['min'] = round(min(__['n']),4)
        result[d]['hash-iters']['max'] = round(max(__['n']),4)

    dt = datetime.datetime.utcnow().replace(microsecond=0)
    fname = 'pow_runtime_stats_{}.txt'.format(dt.isoformat())
    results_path = os.path.join(log_dir,fname)
    with open(results_path,'w') as fd:
        fd.write('{}\n'.format(result))

    return result


if __name__ == '__main__':
    '''
    '''
    pid = os.getpid()
    pid_path = sys.argv[0].split('.py')[0] + '.pid'
    try:
        if os.path.exists(pid_path):
            with open(pid_path,'r') as fd:
                _pid = int(fd.read().strip())
                try:
                    os.kill(_pid,0)
                    msg = 'already got a copy running with pid {}. kill it ... or wait.\n'
                    sys.stderr.write(msg.format(_pid))
                    sys.exit(1)
                except Exception:
                    pass

        with open(pid_path,'w') as fd:
            fd.write('{}\n'.format(pid))

        if len(sys.argv) > 1:
            if sys.argv[1]=='-t' or sys.argv[1]=='--test':
                test_state = test_pow()
                if not test_state:
                    msg = 'looks like you got some work to do: testing failed.\n'
                    sys.stderr.write(msg)
            else:
                msg = 'invalid {} flag. ignored and proceeding.\n'.format(sys.argv[1])
                sys.stdout.write(msg)

        difficulties = [1,2,3,4]
        max_rounds = 1000
        pow_performance_check(difficulties,max_rounds)
        sys.exit(0)
    except KeyboardInterrupt:
        msg = ' really? patience, dude. it just may take a darn long time.\n'
        sys.stderr.write(msg)
        sys.exit(1)
    finally:
        if os.path.exists(pid_path):
            os.remove(pid_path)
