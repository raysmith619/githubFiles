#!/usr/bin/env python
# encoding: utf-8
'''
github_files -- List / Investigate GitHub repositiory files

@author:     Ray Smith

@copyright:  2018 Ray Smith. All rights reserved.

@license:    license

@contact:    raysmith@alum.mit.edu
@deffield    updated: 29Mar2018
'''

import sys
import os
import datetime
from datetime import timezone
from github import Github
from github import InputGitTreeElement
from getpass import getpass
from optparse import OptionParser
import path
import traceback

__all__ = []
__version__ = 0.1
__date__ = '2018-03-27'
__updated__ = '2018-03-27'

DEBUG = 0


"""
Simple tool to facilitate easy object description
"""
            

class obj_desc:
    def __init__(self, obj, *args):
        self.obj = obj
        self.prefix = None
        if len(args) >= 1:
            self.prefix = args[0]
         
      
    def desc(self, att):
        class_str = self.obj.__str__()
        class_name = class_str.split("(")[0]
        prefix = ""
        descr = ""
        att_val = "none"
        if hasattr(self.obj,att):
            attfun = getattr(self.obj, att)
            att_val = attfun
            descr = "%s.%s: %s" % (class_name, att, att_val)
            if self.prefix != None and self.prefix != "":
                prefix = self.prefix + ": "
        print(prefix + descr)  
    
    def descs(self, *atts):
        for att in atts:
            self.desc(att)


"""
Process file
Determine latest commit date for this file in the current branch
"""
class CommittedFile:
    def __init__(self, dir_content_file):
        self.fileName = dir_content_file.name
        self.fileType = dir_content_file.type
        self.fileSize = dir_content_file.size
        self.filePath = dir_content_file.path
        self.fileSha = dir_content_file.sha
        self.key = self.filePath
        self.date = None

"""
Accumulate and access all committed files for a particular branch
File information is stored as required
"""
class CommittedFiles:
    def __init__(self, repo, branchName="master", verbose=0):
        self.repo = repo
        self.branchName = branchName
        self.verbose = verbose
        self.fileDict = {};                 # Stored by path : CommittedFile
        self.nFile = 0
        self.nDated = 0                     # Count of dated
        """
        Add all contained files
        """

                
                
    def collectFile(self, dir_content_file):
        if self.verbose > 0:
            print("%s %s %d %s" %(dir_content_file.name, dir_content_file.type, dir_content_file.size, dir_content_file.path))
        self.addFile(dir_content_file)
            
            
    """
    Get latest commit date for all files in fileDict
    """
    def collectCommitDates(self):
        nshow = 0
        commits = self.repo.get_commits()
        if self.verbose > 0:
            print("%d files" % self.nFile)
        ncommit = 0
        commits = self.repo.get_commits()
        ncommit = 0
        for commit in commits:
            ncommit += 1
        print("%d commits" % ncommit)
            
        contag = "/contents/"
        contag_len = len(contag)
        for commit in commits:
            nshow += 1
            if self.nDated >= self.nFile:
                if self.verbose > 0:
                    print("All %d files have commit dates" % self.nFile)
                    break
                
            if self.verbose > 1:
                cod = obj_desc(commit)
                print("\ncommit %d" % (nshow))
                cod.descs("author", "comments_url", "commit", "committer", "tree", "url")
            git_commit = commit.commit
            git_committer = git_commit.committer
            commit_date = git_committer.date
            comment_str = git_commit.message
            if self.verbose > 0:
                print("commit %d: %s %s %s" % (nshow, commit_date, git_committer.name, comment_str))
            commit_files = commit.files
            for commit_file in commit_files:
                commit_file_name = commit_file.filename
                commit_file_sha = commit_file.sha
                contents_url = commit_file.contents_url
                contents_path = contents_url.split("?")[0]
                path_index = contents_path.find(contag)
                if (path_index < 0):
                    continue
                path = contents_path[path_index+contag_len:]
                key = path
                file = self.fileEntry(key=key)
                if file == None:
                    print("commit %d: file %s(%s) is not in stored files - ignored" % (nshow, path, commit_file_name))
                    print("    %s %s %s" % (commit_date, git_committer, comment_str))
                    continue
 
                if file.date is not None:
                    continue                                # Date already obtained
                
                file_sha = file.fileSha
                if (commit_file_sha != file_sha):
                    if self.verbose > 0:
                        print("%s commit file sha (%s) != file sha(%s) - ignored" % (path, commit_file_sha, file_sha))
                    continue
                file.date = commit_date
                self.nDated += 1
                if self.verbose > 0:
                    print("%s (%s) date: %s   nDate: %d of %d" % (file.fileName, file.filePath, file.date, self.nDated, self.nFile))
        
        n_undated = self.nFile-self.nDated            
        if self.nDated < self.nFile:
            print("%d files have no commit dates" % n_undated)
            for key in self.fileDict:
                file = self.fileEntry(key=key)
                if file is None:
                    print("No entry for key=%s" % key)
                fileDate = file.date
                if fileDate is None:
                    fileName = file.fileName
                    filePath = file.filePath
                    print("    %s (%s)" % (fileName, filePath))
                
                         
    """
    Process directory
    Default - "" - top level directory
    """
    def collectDir(self, dir_content_file=""):
        if hasattr(dir_content_file, "name"):            
            print("%s %s %d %s" %(dir_content_file.name, dir_content_file.type, dir_content_file.size, dir_content_file.path))
            dir_path = dir_content_file.path
        else:
            dir_path = dir_content_file
            
        dir_contents = self.repo.get_dir_contents(dir_path)
        if self.verbose > 0:
            print("dir_path: %s" % (dir_path))
                                                        # First process directories, recursively
        for dir_content_file in dir_contents:
            if dir_content_file.type == "dir":
                self.collectDir(dir_content_file)

        for dir_content_file in dir_contents:
            if dir_content_file.type != "dir":
                self.collectFile(dir_content_file)

                                  
        
        
    """
    """        
    def getCommitDate(self, fileName):
        pass

    """
    Add file to Committed Files
    """        

    def addFile(self, dir_content_file):
        cf = CommittedFile(dir_content_file)
        dict_ent = self.fileEntry(committedFile=cf)
        if dict_ent:
            dict_file_name = dict_ent.fileName
            dict_file_path = dict_ent.filePath
            print("%s name %s path is already present (%s %s) - ignored" % (cf.fileName, cf.filePath, dict_file_name, dict_file_path))
            return
        
        key = cf.filePath    
        self.fileDict[key] = cf
        self.nFile += 1

    """
    Return entry if CommittedFile key matches, else None
    """
    def fileEntry(self, key=None, committedFile=None):
        if key is not None:
            if key in self.fileDict:
                return self.fileDict[key]
            else:
                return None
        
        key = committedFile.key    
        if key in self.fileDict:
            return self.fileDict[key]
        else:
            return None


"""
repo_date to local date string
"""
def repoDateToLocalStr(repo_date):
    repo_time = repo_date.replace(tzinfo=timezone.utc).timestamp()                
    repo_date_str = datetime.datetime.fromtimestamp(repo_time)
    return repo_date_str

"""
repo date to local time stamp
"""
def repoDateToLocalTime(repo_date):
    repo_time = repo_date.replace(tzinfo=timezone.utc).timestamp()                
    return repo_time
 
    
"""    
Commit list from file, base on opts settings
"""
def commit_files(repo, local_file_dir, news, branch=None):
    changed_files = []
    if branch is None:
        branch = "master"
    print("branch: %s" % branch)
    new_file_name = os.path.abspath(news)
    print("Commit file list in %s" % (new_file_name))
    with open(news) as fin:
        for line in fin.readlines():
            line = line.rstrip()      # May have trailing "\"
            changed_files.append(line)
    fin.close()
    print("Changed files:")
    for file in changed_files:
        print("    %s" % file)
    
    commit_lines = []
    print("Commit message - Enter -- to terminate message")
    while True:
        line = sys.stdin.readline().rstrip()
        if line == "--":
            break
        commit_lines.append(line)
    commit_message = "\n".join(commit_lines)
    print("Commit Message: %s" % commit_message)
    if input("Enter 'y' to commit new and changed files:") != 'y':
        print("No commits")
        return
    
    commit_list(repo, local_file_dir, changed_files, branchName=branch, commit_message=commit_message)
    print("Looking at latest commit")
    repo_branch = repo.get_branch(branch)
    commit = repo_branch.commit
    git_commit = commit.commit
    git_committer = git_commit.committer
    repo_date = git_committer.date
    repo_date_str = repoDateToLocalStr(repo_date)
    comment_str = git_commit.message
    print("commit %s %s %s" % (repo_date_str, git_committer.name, comment_str))
    commit_files = commit.files
    for commit_file in commit_files:
        commit_file_name = commit_file.filename
        print("    %s" % commit_file_name)


"""
Commit list of local files to repository
"""
import base64
def commit_list(repo, local_file_dir, localFiles, branchName=None, commit_message=None):
    if branchName is None:
        branchName = 'master'
    if commit_message is None:
        commit_message = input("Commit comment:")
    master_ref = repo.get_git_ref('heads' + "/" + branchName)
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    element_list = list()
    dir_path_len = len(local_file_dir)
    for local_file in localFiles:
        with open(local_file, 'r') as input_file:
            data = input_file.read()
        if local_file.endswith('.png'):
            data = base64.b64encode(data)
        repo_path = local_file[dir_path_len+1:]
        element = InputGitTreeElement(repo_path, '100644', 'blob', content=data)
        element_list.append(element)
    tree = repo.create_git_tree(element_list, base_tree)
    parent = repo.get_git_commit(master_sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])
    master_ref.edit(commit.sha)
    """ An egregious hack to change the PNG contents after the commit """
    for local_file in localFiles:
        if local_file.endswith('.png'):
            old_file = repo.get_contents(local_file)
            with open(local_file, 'rb') as input_file:
                data = input_file.read()
                commit = repo.update_file('/' + local_file, 'Update PNG content', data, old_file.sha)

"""
=================================================================================================================
Support for detailed scan of repository
"""
                
                
def process_file(repo, dir_content_file):
    print("%s %s %d %s" %(dir_content_file.name, dir_content_file.type, dir_content_file.size, dir_content_file.path))
                        
"""
Process directory
"""
def process_dir(repo, dir_content_file):
    if hasattr(dir_content_file, "name"):            
        print("%s %s %d %s" %(dir_content_file.name, dir_content_file.type, dir_content_file.size, dir_content_file.path))
        dir_path = dir_content_file.path
    else:
        dir_path = dir_content_file
        
    dir_contents = repo.get_dir_contents(dir_path)
    print("dir_path: %s" % (dir_path))
                                                    # First process directories
    for dir_content_file in dir_contents:
        if dir_content_file.type == "dir":
            process_dir(repo, dir_content_file)

    for dir_content_file in dir_contents:
        if dir_content_file.type != "dir":
            process_file(repo, dir_content_file)

                                  
def detailed_scan(repo):
    repod = obj_desc(repo)
    repod.desc("name")
    repod.desc("git_url")
    repod.desc("source")
    repod.desc("branches_url")
    repod.desc("contents_url")
    repod.desc("contributors_url")
    repod.desc("events_url")
    repod.desc("default_branch")
    repod.descs("permissions", "private")
    repod.descs("pulls_url", "pushed_at", "size", "source", "ssh_url")
    repod.descs("url", "watchers", "watchers_count")
    repod.descs("trees_url")
    ###repo_tree = repo.get_git_tree(None, True)
    
    repo_url = repo.url;
    print("\nrepo.url: %s" % repo_url)
        
    commits = repo.get_commits()
    ncommit = 0
    for commit in commits:
        ncommit += 1
    print("%d commits" % ncommit)
    nshow = 0
    for commit in commits:
        nshow += 1
        
        cod = obj_desc(commit)
        print("\ncommit %d" % nshow)
        cod.descs("author", "comments_url", "commit", "committer", "tree", "url")
        git_commit = commit.commit
        gcod = obj_desc(git_commit)
        gcod.descs("message", "author", "tree", "url")
        files_str = ""
        for file in commit.files:
            print("")
            fid = obj_desc(file)
            fid.descs("filename", "status", "previous_filename", "contents_url", "raw_url", "additions", "changes")
            if (files_str != ""):
                files_str += ", "
            files_str += file.filename
        print("files: %s" % files_str)
        
        commit_comments = commit.get_comments()
        for comment in commit_comments:
            ccd = obj_desc(comment)
            ccd.descs("body", "commit_id", "created_at")  

"""
=================================================================================================================
"""
    
    
    
def main(argv=None):
    '''Command line options.'''

    program_name = os.path.basename(sys.argv[0])
    program_version = "v0.1"
    program_build_date = "%s" % __updated__

    program_version_string = '%%prog %s (%s)' % (program_version, program_build_date)
    #program_usage = '''usage: spam two eggs''' # optional - will be autogenerated by optparse
    program_longdesc = '''''' # optional - give further explanation about what the program does
    program_license = "Copyright 2018 user_name (organization_name)                                            \
                Licensed under the Apache License 2.0\nhttp://www.apache.org/licenses/LICENSE-2.0"

    if argv is None:
        argv = sys.argv[1:]
    try:
        # setup option parser
        parser = OptionParser(version=program_version_string, epilog=program_longdesc, description=program_license)
        parser.add_option("-a", "--all", dest="all", help="include all files [default: None]")
        parser.add_option("-b", "--branch", dest="branch", help="branch name [default: %default]")
        parser.add_option("-c", "--commlast", dest="commlast", help="just last commits[default: %default], metavar='COMMITS'")
        parser.add_option(      "--commit", dest="commit", action="store_true", default=False, help="just commit[default: None]")
        parser.add_option("-f", "--fullscan", dest="fullScan", help="do full scan[default: %default]")
        parser.add_option("-l", "--local", dest="localFiles", help="get local files [default: <here>/../../<repo>/src")
        parser.add_option("-n", "--new", dest="newfile", help="new files list file [default: parent dir]")
        parser.add_option("-o", "--out", dest="outfile", help="get output file [default: None", metavar="FILE")
        parser.add_option("-p", "--pass", dest="password", help="get user password[default: None], metavar='PASSWORD'")
        parser.add_option("-r", "--repo", dest="repo", help="get repository[default: %default], metavar='REPOSITORY'")
        parser.add_option("-t", "--token", dest="token", help="get login token[default: None], metavar='TOKEN'")
        parser.add_option("-u", "--user", dest="user", help="get user name[default: None], metavar='USER'")
        parser.add_option("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %default]")

        # set defaults
        parser.set_defaults(all=None, commLast=5, fullScan=None,
                            branch="master",
                            localFiles=os.path.join("c:\\Users\\raysm\\workspace\\"),
                            outfile=None, password=None, repo="ExtendedModeler",
                            token=None, user=None, verbose=0)

        # process options
        (opts, args) = parser.parse_args(argv)

        if opts.verbose > 0:
            print("verbosity level = %d" % opts.verbose)
        if not opts.newfile:
            opts.newfile = "new"
            if "." not in opts.newfile:
                opts.newfile += ".commits"
            if not os.path.isabs(opts.newfile):
                opts.newfile = os.path.join("..", opts.newfile)
           
        if opts.outfile:
            if "." not in opts.outfile:
                opts.outfile += ".out"
            if not os.path.isabs(opts.outfile):
                opts.outfile = os.path.join("..", opts.outfile)
            out_file = os.path.abspath(opts.outfile)
            print("outfile = %s" % out_file)
            log = open(opts.outfile, "w")
            stdout_saved = sys.stdout
            sys.stdout = log

        # MAIN BODY #
        gH = None
        """
        User is determined by user + password, if provided,
        else by token, if provided
        else by token in TOKENFILE.txt
        """
        tokenfile = "TOKENFILE.txt";
        tokenfile = os.path.join("..", tokenfile)
        if (opts.token):
            gH = Github(login_or_token=opts.token)
        elif (opts.user):
            if not opts.password:
                opts.password = getpass()                
            gH = Github(opts.user, opts.password)
        elif os.path.exists(tokenfile): 
            ftok = open(tokenfile, "r")
            filetoken = ftok.read()
            gH = Github(login_or_token=filetoken)
        else:
            user = input("Username:")
            password = getpass()
            gH = Github(user, password)
        
        if (not gH):
            raise Exception("Can't get GitHub")  
        
        user = gH.get_user()
        
        if (not opts.repo):
            raise Exception("No repository specified")
        
        print("repository: %s" % opts.repo)
        repo = user.get_repo(opts.repo)
        print("Got repo[%s]" % repo.full_name)
        branches = repo.get_branches()
        branch_names = []
        for branch in branches:
            branch_names.append(branch.name)
        branches_str = ", ".join(branch_names)
        print("branches: %s" % (branches_str))
        branch_name = opts.branch
        if not branch_name in branch_names:
            print("branch name: %s is not in your branches: %s" % (branch_name, branches_str))
            sys.exit(1)
            
        default_branch = repo.default_branch
        print("default branch: %s" % default_branch)
        if branch_name is None:
            branch_name = default_branch
        print("Using branch: %s" % branch_name)
        branch = repo.get_branch(branch_name)
        branch_commit = branch.commit
            
        local_files_spec = os.path.join(opts.localFiles, opts.repo)
        local_file_dir = os.path.abspath(local_files_spec)
        lsrc = os.path.join(local_file_dir, "src")
        if os.path.exists(lsrc) and os.path.isdir(lsrc):
            local_file_dir = lsrc
            print("Using \"src\" sub directory for files")
        print("Local files: %s" % local_file_dir)
        
        if (opts.commit):
            commit_files(repo, local_file_dir, opts.newfile, branch=opts.branch)        # Just commit from new file list
            print("Commit Done")
            exit(0)
            
        if opts.fullScan:
            detailed_scan()
        cF = CommittedFiles(repo, verbose=opts.verbose)
        cF.collectDir()
        cF.collectCommitDates()
        print("%d files of %d have commit dates" % (cF.nDated, cF.nFile))
        """
        Scanning local files, checking for updates
        """
        changed_files = []
        for foldername, subfolders, filenames in os.walk(local_file_dir):
            print("Checking files in %s..." % (foldername))
            ldir = foldername[len(local_file_dir)+1:]
            # Add all the files in this folder
            for filename in filenames:
                lfilepath = os.path.join(foldername, filename)
                lpath = os.path.join(local_file_dir, ldir, filename)
                if not os.path.exists(lpath):
                    print("Can't find path %s - ignored" % lpath)
                    continue

                rpath = lpath[len(local_file_dir)+1:].replace("\\", "/", 99)
                if opts.verbose > 0:
                    print("%s" % rpath)
                fentry = cF.fileEntry(key=rpath)
                if (not fentry):
                    print("%s not in repository ==> New" % rpath)
                    changed_files.append(lpath)     # Add to list
                    continue

                repo_date = fentry.date
                repo_date_str = repoDateToLocalStr(repo_date)
                repo_time = repoDateToLocalTime(repo_date)
                ltime = os.path.getmtime(lpath)
                ltime_str = datetime.datetime.fromtimestamp(ltime)
                if opts.verbose > 0:
                    print("%s %s repo: '%s'" % (rpath, ltime_str, repo_date_str))
                #lfile = datetime.datetime.strptime(linx_file_dtime[:-3], '%Y-%m-%d_%H:%M:%S.%f')
                if ltime > repo_time:
                    print("%s local is newer %s than repo %s" % (rpath, ltime_str, repo_date_str))
                    changed_files.append(lpath)     # Add to list
        if len(changed_files) > 0:
            commit_list_file = os.path.abspath(opts.newfile)
            print("Changed file list is in %s" % commit_list_file)
            fout = open(commit_list_file, 'w')
            out_str = "\n".join(changed_files)
            fout.write(out_str)
            fout.close()
            
            commit_files(repo, local_file_dir, opts.newfile, branch=opts.branch)        # Just commit from new file list
        else:
            print("No new or changed files")
            
        print("Done")
        if opts.outfile:
            sys.stdout = stdout_saved
            print("Output is in %s" % out_file)
        
            
    except Exception as e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        traceback.print_stack(e)
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    sys.exit(main())