
main.formula <- innovation~h1.1+h2.1+h3.1+h3.2+h3.3+h3.4+(1|matchid)
weak_prior <- cauchy(0, 2.5)

# Train the model
glmmoverall <- stan_glmer(main.formula, data=factorial, family = binomial(link = "logit"),
                          prior = weak_prior, prior_intercept = weak_prior,
                          diagnostic_file = "df1.csv")

test.data1 <- expand.grid(h1.1=1,
                          h2.1=c(0,1),
                          h3.1=c(0,1),
                          h3.2=c(0,1),
                          h3.3=9,
                          h3.4=c(0,1))

test.data2 <- expand.grid(h1.1=c(2, 3, 4),
                          h2.1=c(0,1),
                          h3.1=c(0,1),
                          h3.2=c(0,1),
                          h3.3=seq(1:4),
                          h3.4=c(0,1))
test.data<-rbind(test.data1, test.data2)

test.data$matchid <- 1
test.data <- data.frame(lapply(test.data, factor))

levels(test.data$h1.1) <- levels(factorial$h1.1)
test.data$matchid <- factorial$matchid[1]
levels(test.data$matchid) <- levels(factorial$matchid)

S = 1000 # number of Monte Carlo draws from p(w|D) where D is the initial set of observed data

x = test.data
ppdx = posterior_linpred(glmmoverall,newdata = x,transform = TRUE)[1:S,]

prob = (1/S * colSums(ppdx))*(1-1/S * colSums(ppdx))

rank.var <- order(prob,decreasing = TRUE)

x.ranked.var = x[rank.var,]
x.ranked.var <- cbind(x.ranked.var,prob[rank.var])

x.ranked.var$matchid <- NULL
x.ranked.var$h1.3 <- NULL

colnames(x.ranked.var) <- c("h1.1","h2.1","h3.1","h3.2","h3.3","h3.4","variance")
data.frame(x.ranked.var)
write.csv(x.ranked.var, file = "gamesData_ranked-criterion1_noTools.csv")

P0.mat = posterior_linpred(glmmoverall,newdata = x,transform = TRUE)[1:S,] # ppdx
term1=rep(0,ncol(P0.mat))
term2=rep(0,ncol(P0.mat))

for (i in 1:ncol(P0.mat)){
  term1[i] = -(1/S)*(sum(P0.mat[,i]*log(P0.mat[,i]))+sum((1-P0.mat[,i])*log(1-P0.mat[,i])))
  term2[i] = log(1/S *sum(P0.mat[,i]))*(1/S *sum(P0.mat[,i])) + log(1/S *sum(1-P0.mat[,i]))*(1/S *sum(1-P0.mat[,i]))
}

post.entropy = term1 + term2

rank.post.entropy <- order(post.entropy,decreasing = FALSE)
x.ranked.post.entropy = x[rank.post.entropy,]
x.ranked.post.entropy <- cbind(x.ranked.post.entropy,post.entropy[rank.post.entropy])
x.ranked.post.entropy$matchid <- NULL
x.ranked.post.entropy$h1.3 <- NULL


colnames(x.ranked.post.entropy) <- c("h1.1","h2.1","h3.1","h3.2","h3.3","h3.4","entropy")
data.frame(x.ranked.post.entropy)
write.csv(x.ranked.post.entropy, file = "gamesData_ranked-criterion2_noTools.csv")
