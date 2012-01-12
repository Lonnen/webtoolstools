#!/usr/bin/python
"""
give me a pair of git revisions and a bugzilla target milestone, and I'll show you
the difference.

Example: ./gitzilla.py --target-milestone=2.4 --old-rev=v2.3.5.1 --new-rev=master
"""

import re
import sys
import optparse
import urllib2
import csv
import subprocess

bug_pattern = re.compile(r'bug\s?\d+', flags=re.IGNORECASE)
bz_baseurl = 'https://bugzilla.mozilla.org/buglist.cgi?query_format=advanced&target_milestone=%s&product=Socorro&ctype=csv'

def compare(git_bug_nums, target_milestone):
    bz_url = bz_baseurl % target_milestone

    bug_reports = csv.DictReader(urllib2.urlopen(bz_url))
    bz_bug_nums = set(x['bug_id'] for x in bug_reports)

    for num in (git_bug_nums & bz_bug_nums):
        print 'OK %s in git is in target milestone %s' % (num, target_milestone)

    for num in (bz_bug_nums - git_bug_nums):
        print 'WARNING %s is in target milestone %s but not in git' % (num, target_milestone)

    for num in (git_bug_nums - bz_bug_nums):
        print 'ERROR %s is in git but not in target milestone %s' % (num, target_milestone)

def main(target_milestone, old_rev, new_rev):
    git_bugs = gitbugs(old_rev, new_rev) - gitbugs(new_rev, old_rev)
    compare(git_bugs, target_milestone)

def gitbugs(from_rev, to_rev):
    git_log_args = ['git', 'log', '--oneline', '%s..%s' % (from_rev, to_rev)]
    print 'Running: %s' % ' '.join(git_log_args)
    process = subprocess.Popen(git_log_args, stdout=subprocess.PIPE)
    process.wait()
    if process.returncode != 0:
        print 'git exited non-zero: %s' % process.returncode
        sys.exit(1)

    git_bugs = set()
    for line in process.stdout:
        commit_msg = line.strip()
        bug_msg = bug_pattern.findall(commit_msg)
        if bug_msg is None:
            print 'ERROR missing bug message in git log: %s' % commit_msg
        else:
            git_bugs = git_bugs.union(
              set(x.lower().split('bug')[1].strip() for x in bug_msg))

    return git_bugs

if __name__ == '__main__':
    usage = "%prog [options] args_for_git_log"
    parser = optparse.OptionParser("%s\n%s" % (usage.strip(), __doc__.strip()))
    parser.add_option('-t', '--target-milestone', dest='target_milestone',
                      type='string', help='target_milestone to check on bz')
    parser.add_option('-o', '--old-rev', dest='old_rev',
                      type='string', help='old git revision')
    parser.add_option('-n', '--new-rev', dest='new_rev',
                      type='string', help='new git revision')
    (options, args) = parser.parse_args()

    mandatories = ['target_milestone', 'old_rev', 'new_rev']
    for m in mandatories:
        if not options.__dict__[m]:
            print "mandatory option is missing\n"
            parser.print_help()
            sys.exit(-1)

    target_milestone = options.target_milestone
    old_rev = options.old_rev
    new_rev = options.new_rev

    main(target_milestone, old_rev, new_rev)
