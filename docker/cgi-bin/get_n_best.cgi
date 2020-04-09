#!/usr/bin/perl
#mihael.arcan@deri.org

use strict;
use warnings;
use Data::Dumper;
use Benchmark;

use Storable;
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);

use Encode;
use URI::Escape;
use utf8;

my $t0 = new Benchmark;

read(STDIN, my $entry, $ENV{'CONTENT_LENGTH'});

$entry = uri_unescape($entry);
my ($source,$num,$t) = $entry =~ /^(.+?)\|\|\|(\d+)\|\|\|(.+?)=n/;


		

print "Content-type: text/html\n\n";
print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">', "\n";
print "<html>\n<head>\n<title></title>\n";
print "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>\n";
print "<meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\">\n";
print "<meta http-equiv=\"content-type\" content=\"application/xhtml+xml; charset=UTF-8\">\n";
print "<meta http-equiv=\"content-style-type\" content=\"text/css\">\n";
print "<meta http-equiv=\"expires\" content=\"0\">\n";
print "<script src=\"/home/miharc/public_html/cgi-bin/sorttable.js\"></script>\n";
print "</head>\n";
print "<body>\n";

#print "$entry"; exit;

my $if_clesa = 0;
open my $in, "<", $t or die "Error/read $!";
undef $/; my $file = <$in>; $/="\n";	
if ($file =~ /\|\|\ clesa/) {
	$if_clesa = 1;
}

$source =~ s/\+/ /g;
utf8::decode($source);
print "<table border=\"0\" width=\"100%\">";

print "<table border=\"2\" width=\"100%\">";
print "<tr><th colspan=\"2\">Source</th></tr>\n";
print "<tr><td colspan=\"2\">$source</td></tr>\n";
print "</table>";


#print "<div style=\"height:530px;overflow:auto;\">";
print "<table class=\"sortable\" border=\"2\" style=\"height:90%;overflow:auto;\"width=\"100%\">\n"; 
print "<thead>\n";
if ($if_clesa == 0) {
	print "<tr><th>Target</th><th>Prob</th></tr>\n";
} else {
	print "<tr><th>Target</th><th>Prob</th><th>CLESA</th></tr>\n";
}

print "</thead>\n";
print "<tbody>\n";


open my $in, "<", $t or die "Error/read $!";
while (my $line =<$in>) {
	chomp($line);
	if ($line =~ /\|\sclesa:\s\d\.\d+$/) {
		my ($id, $nbest, $p, $clesa) = $line =~ /^(\d+)\s\|\|\|\s+(.+?)\s+\|\|\|.+\|\|\|\s(.+?)\s\|\|\|\sclesa:\s+(.+?)$/;
		if ($id == $num) {
			print "<tr><td>$nbest</td><td>$p</td><td>$clesa</td></tr>\n";
		}
		last if ($id > $num);
	} else {
		my ($id, $nbest, $p) = $line =~ /^(\d+)\s\|\|\|\s+(.+?)\s+\|\|\|.+\|\|\|\s(.+?)$/;
		if ($id == $num) {
			print "<tr><td>$nbest</td><td>$p</td></tr>\n";
		}
		last if ($id > $num);
	}
	
}

print "</tbody>\n";
print "</table>\n";
#print "</div>";
print "</table>\n";

print "</body>\n";
print "</html>";


