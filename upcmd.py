#!/usr/bin/env python
# *-* coding: utf-8 *-*

import os
import sys
import uuid
import signal
import datetime
import optparse

from cmd import Cmd

from upyun import UpYun, UpYunClientException, UpYunServiceException
from util import basename, isdir, walk, exists, pretty_print


class Shell(Cmd):
    prompt = "(upcmd) "
    intro = "Welcome to Upyun Cmd"

    def __init__(self, up):
        self.up = up
        self.current = "/"
        Cmd.__init__(self)

    def completedefault(self, *ignore):
        path = self.current
        ret = []
        _, dirs, files = walk(self.up, path)
        ret.extend(dirs)
        ret.extend(files)
        return ret

    """
    def complete_cd(self, text):
        _, dirs, _ = walk(self.up, self.current)
        if not text:
            completions = dirs
        else:
            completions =[d for d in dirs if d.startswith(text)]
        return completions
    """
    def help_cd(self):
        print '''This command is use for changing directory.'''

    def do_cd(self, arg):
        if arg == "":
            self.current = "/"
        elif arg == "..":
            self.current = os.path.dirname(self.current)
        elif isdir(self.up, arg):
            self.current = os.path.join(self.current, arg)
        else:
            tmp = os.path.join(self.current, arg)
            if isdir(self.up, tmp):
                self.current = tmp

    def help_local(self):
        print "This command is use for excuting command on you own PC"

    def do_local(self, arg):
        os.system(arg)

    def help_pwd(self):
        print "This command is use for displaying the current path"

    def do_pwd(self, arg):
        print self.current

    def help_ls(self):
        print "This command is use for listing all of the item in current path"

    def do_ls(self, arg):
        Lst(self.up, self.current)

    def do_put(self, arg):
        src, dst = arg.split()

        if os.path.exists(src):
            pass
        else:
            src = os.path.join(os.getcwd(), src)

        if not os.path.exists(src):
            return

        if exists(self.up, dst):
            pass
        else:
            dst = os.path.join(self.current, dst)

        Put(self.up, src, dst)

    def do_get(self, arg):
        src, dst = arg.split()

        if exists(self.up, src):
            pass
        else:
            src = os.path.join(self.current, src)

        if os.path.exists(dst):
            pass
        else:
            dst = os.path.join(os.getcwd(), dst)

        Get(self.up, src, dst)

    def do_mkdir(self, arg):
        src = os.path.join(self.current, arg)

        if not exists(self.up, src):
            Mkd(self.up, src)

    def do_rm(self, arg):
        src = os.path.join(self.current, arg)

        if not exists(self.up, src):
            pass
        else:
            Del(self.up, src)

    def do_rename(self, arg):
        src, dst = arg.split()

        src = os.path.join(self.current, src)
        dst = os.path.join(self.current, dst)

        if not exists(self.up, src):
            return
        else:
            Rename(self.up, src, dst)

# --- complex operation ---


def Rename(up, src, dst):
    tmp = "/tmp/upcmd-" + uuid.uuid4().hex

    err = False

    err = Get(up, src, tmp, output=False)
    if err:
        return err

    err = Put(up, tmp, dst, output=False)
    if err:
        return err

    err = Del(up, src, ask=False, output=False)
    if err:
        return err

    try:
        os.remove(tmp)
    except:
        pass

    return err


def Puts(up, src, dst):
    err = False
    dst = os.path.join(dst, basename(src))
    err = Mkd(up, dst)

    if err:
        return err
    for root, dirs, files in os.walk(src):
        for name in files:
            src_name = os.path.join(root, name)
            dst_name = os.path.join(dst, name)
            err = Put(up, src_name, dst_name)
            if err:
                return err
        for name in dirs:
            src_dir = os.path.join(root, name)
            err = Puts(up, src_dir, dst)
            if err:
                return err
        break


def Gets(up, src, dst):
    err = False
    dst = os.path.join(dst, basename(src))
    try:
        os.mkdir(dst)
    except:
        err = True

    if err:
        return err
    root, dirs, files = walk(up, src)
    for name in files:
        src_name = os.path.join(root, name)
        dst_name = os.path.join(dst, name)
        err = Get(up, src_name, dst_name)
        if err:
            return err

    for name in dirs:
        src_dir = os.path.join(root, name)
        err = Gets(up, src_dir, dst)
        if err:
            return err


# --- simple operation ----

def Put(up, src, dst, output=True):
    # i'm so damn like python
    if os.path.isdir(src) and isdir(up, dst):
        return Puts(up, src, dst)

    if os.path.isdir(src) and not isdir(up, dst):
        return True

    if os.path.isfile(src) and isdir(up, dst):
        dst += basename(src)

    err = False
    try:
        f = open(src, "rb")
        up.put(dst, f)
        if output:
            print src, "====>>>", dst
    except:
        err = True

    f.close()
    if err and output:
        print "Upload Error"
        return err


def Get(up, src, dst, output=True):
    if isdir(up, src) and os.path.isdir(dst):
        return Gets(up, src, dst)

    if isdir(up, src) and not os.path.isdir(dst):
        return False

    if not isdir(up, src) and os.path.isdir(dst):
        dst += basename(src)

    err = False
    try:
        f = open(dst, "wb")
        up.get(src, f)
        if output:
            print src, "====>>>", dst
    except:
        err = True

    f.close()
    if err and output:
        print "Download Error"
        return err


def Del(up, dst, ask=True, output=True):
    if ask:
        ans = raw_input("do you want to remove %s? (yes/no) " % dst)
        if ans == "yes":
            pass
        else:
            return
    err = False
    try:
        up.delete(dst)
    except:
        if output:
            print "Delete Error"
        err = True

    return err


def Mkd(up, dst, output=True):
    err = False
    try:
        up.mkdir(dst)
    except:
        if output:
            print "Mkdir Error"
        err = True

    return err


def Lst(up, dst, output=True):
    err = False
    ret = None
    try:
        ret = up.getlist(dst)
    except:
        err = True

    if err and output:
        print "List Error"

    if not err and output:
        pretty_print(ret)

    return err


def Parser():
    usage = "bla bla bla"
    parser = optparse.OptionParser(usage)

    parser.add_option("-b", "--bucket", dest="bucket",
                      help="The bucket name")
    parser.add_option("-p", "--passwd", dest="passwd",
                      help="The passwd of yours")
    parser.add_option("-u", "--user", dest="user",
                      help="The user name")
    parser.add_option("-i", action="store_true", default=False,
                      dest="interactive")
    parser.add_option("--put", type="string", nargs=2,
                      dest="put")
    parser.add_option("--get", type="string", nargs=2,
                      dest="get")
    parser.add_option("--rename", type="string", nargs=2,
                      dest="rename")
    parser.add_option("--rm", type="string",
                      dest="rm")
    parser.add_option("--mkdir", type="string",
                      dest="mkdir")
    parser.add_option("--ls", type="string",
                      dest="ls")
    return parser


def Interactive(up):
    shell = Shell(up)
    stop = False
    while not stop:
        try:
            shell.cmdloop()
        except:
            print "Cmd crashed and Restart"


def handle(up, options):
    if options.put:
        return Put(up, options.put[0], options.put[1])
    if options.get:
        return Get(up, options.get[0], options.get[1])
    if options.rename:
        return Rename(up, options.rename[0], options.rename[1])
    if options.rm:
        return Del(up, options.rm)
    if options.mkdir:
        return Mkd(up, options.mkdir)
    if options.ls:
        return Lst(up, options.ls)


def init_signal():
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def main():
    parser = Parser()
    (options, args) = parser.parse_args()
    err = False

    init_signal()

    try:
        up = UpYun(options.bucket,
                   options.user,
                   options.passwd)
        res = up.usage()
    except UpYunClientException as e:
        err = True
        print "ClientError: " + e.message
    except UpYunServiceException as e:
        err = True
        print "ServiceError: " + e.message
    except:
        err = True

    if err:
        print "failed when log in ..."
        return

    if len(args) != 0:
        parser.error("Unexcepted arguments")
        sys.exit(0)

    if options.interactive:
        Interactive(up)
    else:
        handle(up, options)

if __name__ == "__main__":
    main()
