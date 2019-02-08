## Created by Pablo Diego Rosell, PhD, for Gallup inc. in September 2018
## For any questions, contact pablo_diego-rosell@gallup.co.uk

options(error=traceback)

# Read in data
if('gamesData.csv' %in% list.files(paste(od, sep = '/'))) {
  factorial <- read.csv(file = paste(od, "gamesData.csv", sep = '/'))
} else {
  stop('WARNING - Metadata is missing; download by hand and merge to continue.')
}
factorial<-data.frame(lapply(factorial, factor))
factorial$round<-as.numeric(factorial$round)

# Number of valid games
nGames<-length(unique(factorial$matchid))
groups<- factorial[!duplicated(factorial$matchid),]
replays<-table(groups$consumableKey)

# Number of players connected
factorial$nConnected<-as.numeric(levels(factorial$nConnected))[factorial$nConnected]
nConnected<-aggregate(nConnected ~ matchid, data=factorial, mean)
nPlayers<-sum(nConnected$nConnected)

# Game dates
factorial$date.time<-as.Date(levels(factorial$date.time))[factorial$date.time]
dates<-aggregate(date.time ~ matchid, data=factorial, mean)

# Number of unique experimental conditions played
factorial$settingsNum<-as.numeric(levels(factorial$settingsNum))[factorial$settingsNum]
nConditions<-length(unique(factorial$settingsNum))

# List of conditions played
settingsNum<-aggregate(settingsNum ~ matchid, data=factorial, first)
factorial$replay<-"Replay"
factorial$replay[factorial$consumableKey=="prod_high_0_firsttime" |
                   factorial$consumableKey=="prod_high_1_firsttime" |
                   factorial$consumableKey=="prod_low_0_firsttime"  |
                   factorial$consumableKey=="prod_low_1_firsttime"]<-"first time"
replays<-aggregate(replay ~ matchid, data=factorial, first)
settingsReplayed <- merge(settingsNum,replays,by="matchid")
settingsNumTab<-table(settingsReplayed$settingsNum, settingsReplayed$replay)
settingsNumTab<-as.data.frame.matrix(settingsNumTab)
settingsNumTab<-tibble::rownames_to_column(settingsNumTab, var = "settingsNum")
write.csv(settingsNumTab, paste(od, "settingsNumTab.csv", sep = '/'))

# List of conditions pending
allConditions<-1:208
playedConditions<-unique(factorial$settingsNum)
pendingConditions<-setdiff(allConditions, playedConditions)
pendingConditions<-as.data.frame(pendingConditions)
colnames(pendingConditions)<-c("settingsNum")
write.csv(pendingConditions, paste(od, "pendingConditions.csv", sep = '/'))

# Bayesian GLMM function

main.formula <- innovation~h1.1+h1.3+h2.1+h3.1+h3.2+h3.3+h3.4+h3.5+tools+(1|matchid)
weak_prior <- normal(0, 2.5)

bayesGlmer<-function(formula, priors) {
  set.seed(12345)
  pathdf<-paste(deparse(substitute(priors)),".csv", sep="")
  fittedGlmer<- stan_glmer(formula,
                           data=factorial,
                           family = binomial(link = "logit"),
                           prior = priors,
                           prior_intercept = weak_prior,
                           chains = 3, iter = nIter,
                           diagnostic_file = pathdf)
  return(fittedGlmer)
}

# Bayesian plotting functions

modelPlotter<- function (model, ivs) {
  posterior <- as.array(model)
  mcmc_areas(posterior, pars = ivs,
             prob = 0.8, # 80% intervals
             prob_outer = 0.99, # 99%
             point_est = "mean")
}

bayesPlotter <- function (plotdf, plotBF) {
  frame.posterior<-subset(plotdf, Distribution=="Posterior")
  postPlot<-ggplot(frame.posterior, aes(value, fill=Level, linetype=Distribution)) +
    geom_density(alpha=0.4) +
    scale_x_continuous(limits = c(-5, 5)) +
    scale_y_continuous(limits = c(0, 5))
  bfPlot<-ggplot(plotdf, aes(value, fill=Level, linetype=Distribution)) +
    geom_density(alpha=0.4) +
    scale_x_continuous(limits = c(-5, 5)) +
    scale_y_continuous(limits = c(0, 5)) +
    annotate("text", x=2, y=1.7, label = paste(deparse(substitute(plotBF)), " = ", sprintf("%0.2f", plotBF))) +
    geom_vline(xintercept = 0, linetype="dashed")
  return(list(postPlot, bfPlot))
}

# Bayesian plotting - frame processing function (Predictions with two coefficients)

bayesPlotter1 <- function (model, priors1, priorScale, coef1, plotBF) {
  plotIters<-nIter*1.5
  draws <- as.data.frame(model)
  a <- rnorm(plotIters, mean=logodds[[priors1]], sd=priorScale)
  d <- draws[[coef1]]
  plotdf <- data.frame(value=c(a, d),
                       Distribution=c(rep("Prior", plotIters),
                                      rep("Posterior", plotIters)),
                       Level=c(rep(priors1, plotIters),
                               rep(priors1, plotIters)))
  plots<-bayesPlotter(plotdf, plotBF)
  return(plots)
}

bayesPlotter2 <- function (model, priors1, priors2, priorScale, coef1, coef2, plotBF) {
  plotIters<-nIter*1.5
  draws <- as.data.frame(model)
  a <- rnorm(plotIters, mean=logodds[[priors1]], sd=priorScale)
  b <- rnorm(plotIters, mean=logodds[[priors2]], sd=priorScale)
  d <- draws[[coef1]]
  e <- draws[[coef2]]
  plotdf <- data.frame(value=c(a, b, d, e),
                       Distribution=c(rep("Prior", plotIters*2),
                                      rep("Posterior", plotIters*2)),
                       Level=c(rep(priors1, plotIters),
                               rep(priors2, plotIters),
                               rep(priors1, plotIters),
                               rep(priors2, plotIters)))
  plots<-bayesPlotter(plotdf, plotBF)
  return(plots)
}

# Bayesian plotting - frame processing function (Predictions with three coefficients)

bayesPlotter3 <- function (model, priors1, priors2, priors3, priorScale, coef1, coef2, coef3, plotBF) {
  plotIters<-nIter*1.5
  draws <- as.data.frame(model)
  a <- rnorm(plotIters, mean=logodds[[priors1]], sd=priorScale)
  b <- rnorm(plotIters, mean=logodds[[priors2]], sd=priorScale)
  c <- rnorm(plotIters, mean=logodds[[priors3]], sd=priorScale)
  d <- draws[[coef1]]
  e <- draws[[coef2]]
  f <- draws[[coef3]]
  plotdf <- data.frame(value=c(a, b, c, d, e, f),
                       Distribution=c(rep("Prior", plotIters*3),
                                      rep("Posterior", plotIters*3)),
                       Level=c(rep(priors1, plotIters),
                               rep(priors2, plotIters),
                               rep(priors3, plotIters),
                               rep(priors1, plotIters),
                               rep(priors2, plotIters),
                               rep(priors3, plotIters)))
  plots<-bayesPlotter(plotdf, plotBF)
  return(plots)
}

# Overall glmm for main effects in full-factorial space

glmmoverall <- bayesGlmer(main.formula, weak_prior)
glmmoverall
nCoef<-lengths(dimnames(glmmoverall$covmat)[1])

overallIvs<-c("h1.11","h1.12","h1.13","h1.31","h1.32",
              "h2.11","h3.11","h3.21","h3.32","h3.33","h3.34",
              "h3.41","h3.51","h3.52","tools2","tools3","tools4",
              "tools5","tools6","tools7","tools8")

posteriorAreas<-modelPlotter(glmmoverall, overallIvs)
