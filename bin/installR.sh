#!/usr/bin/bash
echo 'local({
  r <- getOption("repos")
  r["CRAN"] <- "http://cran.cnr.berkeley.edu/"
  options(repos = r)
})' >> /etc/R/Rprofile.site
chmod -R 777 /usr/local/lib/R/site-library
R -e 'Sys.setenv(MAKEFLAGS = "-j4"); install.packages(c("multiwayvcov","lmtest","dplyr","rstan"),dependencies=TRUE)'
