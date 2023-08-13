# -*- coding: utf-8 -*-
"""Group 1 Part 2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1sl9rDVXCAT-8eaEyIHyRiUxU5iPGfbrM

# Dataset
"""

# Importing data from Excel
library("readxl")
df <- as.data.frame(read_excel("rainfall 50mm.xlsx"))
# rainfall <- df[["Total"]]
# rainfall

x <- df[,14]
d <- df[,1]
n <- length(x)

# install.packages('HiddenMarkov')

# simulate
library("HiddenMarkov")

# length of the simulated data
nsim <- 100
# set seed
seed <- 40112

# nstate = 2
# transition probability matrix of Markov chain
Pi_2 <- rbind(c(.8,.2), c(.1,.9))
# initial distribution of Markov chain
delta_2 <- c(.5,.5)
# Poisson parameter
lambda_2 <- c(10,20)

# cerating HMM object
model1 <- dthmm(NULL, Pi=Pi_2, delta=delta_2, "pois", list(lambda=lambda_2))
# simulating data
simulate1 <- simulate(model1, nsim=nsim, seed=seed)
simulate1$x

plot(simulate1$x)
hist(simulate1$x, freq=FALSE, main='')
summary(simulate1$x)
sqrt(var(simulate1$x))

#nstate = 3
# transition probability matrix of Markov chain
Pi_3 <- rbind(c(.8,.2,.0), c(.0,.0,1), c(.7,.3,.0))
# initial distribution of Markov chain
delta_3 <- c(1/3,1/3,1/3)
# Poisson parameter
lambda_3 <- c(10,20,30)

# cerating HMM object
model3 <- dthmm(NULL, Pi=Pi_3, delta=delta_3, "pois", list(lambda=lambda_3))
# simulating data
simulate3 <- simulate(model3, nsim=nsim, seed=seed)
simulate3$x

plot(simulate3$x)
hist(simulate3$x, freq=FALSE, main='')
summary(simulate3$x)
sqrt(var(simulate3$x))

#self-written code
pois.HMM.sample <- function(n, pi, delta, lambda){
  X <- rep(NA, n)
	Y <- rep(NA, n)
	nstate <- 1:length(delta)
	Y[1] <- sample(nstate,1 , prob=delta)
	for (i in 2:n){
	  Y[i] <- sample(nstate, 1, prob=pi[Y[i-1],])
		X <- rpois(n, lambda=lambda[nstate])
		}
  out <- cbind(X,Y)
	return(out)
}
set.seed(40112)
# 2-state
pois.HMM.sample(n, pi_2, delta_2, lambda_2)
# 3-state
pois.HMM.sample(n, pi_3, delta_3, lambda_3)

#Simulated data
rainfall<-c(7,17,13,23,15,18,21,14,18,18,21,16,17,14,19,17,22,17,20,20,
            20,27,23,11,16,16,25,22,26,14,22,15,25,16,26,22,21,16,21,12,
            15,25,18,19,17,20,17,24,30,17,16,11,9,12,14,22,15,3,4,14,
            15,26,14,5,13,9,9,8,8,12,20,19,18,19,17,12,21,7,29,22,
            18,19,15,19,22,24,11,20,21,26,21,23,18,20,24,20,16,20,19,18)

rainfall2<-c(26,30,5,33,15,27,25,36,18,9,31,16,27,14,29,17,33,17,10,10,
             30,27,12,19,16,25,25,33,26,22,22,6,14,26,26,33,21,26,21,5,
             6,13,8,9,26,20,7,13,17,27,16,11,9,20,14,11,24,11,19,25,
             6,38,14,5,13,29,18,27,22,27,19,28,19,27,12,11,25,29,11,9,
             29,15,28,22,35,22,10,31,26,32,23,27,12,30,16,30,19,28,14,23)

"""# Various functions for parameter transformation, likelihood computation"""

#====================================== transforming natural parameters to working
pois.HMM.pn2pw <- function(m,lambda,gamma,delta=NULL, stationary=TRUE){
  tlambda <- log(lambda)
  if(m==1) return(tlambda)
  foo <- log(gamma/diag(gamma))
  tgamma <- as.vector(foo[!diag(m)])
  if(stationary) {tdelta <- NULL}
    else {tdelta <- log(delta[-1]/delta[1])}
  parvect <- c(tlambda,tgamma,tdelta)
  return(parvect)
}

#====================================== transforming working parameters to natural
pois.HMM.pw2pn <- function(m,parvect,stationary=TRUE){
  lambda <- exp(parvect[1:m])
  gamma <- diag(m)
  if (m==1) return(list(lambda=lambda,gamma=gamma,delta=1))
  gamma[!gamma] <- exp(parvect[(m+1):(m*m)])
  gamma <- gamma/apply(gamma,1,sum)
  if(stationary){delta<-solve(t(diag(m)-gamma+1),rep(1,m))}
    else {foo<-c(1,exp(parvect[(m*m+1):(m*m+m-1)]))
    delta<-foo/sum(foo)}
  return(list(lambda=lambda,gamma=gamma,delta=delta))
}

#====================================== computing minus the log-likelihood from the working parameters
pois.HMM.mllk <- function(parvect,x,m,stationary=TRUE,...){
  if(m==1) return(-sum(dpois(x,exp(parvect),log=TRUE)))
  n <- length(x)
  pn <- pois.HMM.pw2pn(m,parvect,stationary=stationary)
  foo <- pn$delta*dpois(x[1],pn$lambda)
  sumfoo <- sum(foo)
  lscale <- log(sumfoo)
  foo <- foo/sumfoo
  for (i in 2:n){
    if (!is.na(x[i])){P<-dpois(x[i],pn$lambda)}
      else {P<-rep(1,m)}
    foo <- foo %*% pn$gamma*P
    sumfoo <- sum(foo)
    lscale <- lscale+log(sumfoo)
    foo <- foo/sumfoo
  }
  mllk <- -lscale
  return(mllk)
}

#====================================== computing the MLEs, given starting values for the natural parameters
pois.HMM.mle <- function(x,m,lambda0,gamma0,delta0=NULL,stationary=TRUE,...){
  parvect0 <- pois.HMM.pn2pw(m,lambda0,gamma0,delta0,stationary=stationary)
  mod <- nlm(pois.HMM.mllk,parvect0,x=x,m=m,stationary=stationary)
  pn <- pois.HMM.pw2pn(m=m,mod$estimate,stationary=stationary)
  mllk <- mod$minimum
  np <- length(parvect0)
  AIC <- 2*(mllk+np)
  n <- sum(!is.na(x))
  BIC <- 2*mllk+np*log(n)
  list(m=m, lambda=pn$lambda,gamma=pn$gamma,delta=pn$delta,code=mod$code,mllk=mllk,AIC=AIC,BIC=BIC)
}

#====================================== computing log(forward probabilities)
pois.HMM.lforward<-function(x,mod){
  n <- length(x)
  lalpha <- matrix(NA,mod$m,n)
  foo <- mod$delta*dpois(x[1],mod$lambda)
  sumfoo <- sum(foo)
  lscale <- log(sumfoo)
  foo <- foo/sumfoo
  lalpha[,1] <- lscale+log(foo)
  for (i in 2:n){
    foo <- foo%*%mod$gamma*dpois(x[i],mod$lambda)
    sumfoo <- sum(foo)
    lscale <- lscale+log(sumfoo)
    foo <- foo/sumfoo
    lalpha[,i] <- log(foo)+lscale
  }
  return(lalpha)
}

"""# Fitting Possion HMM"""

#Possion_HMM
#MLE+BW
library("HiddenMarkov")
#nstate = 2 (non-stationary case)
Pi <- rbind(c(.8,.2),c(.1,.9))
mod <- dthmm(rainfall,Pi=Pi,delta=c(.5,.5),"pois", list(lambda=c(10,20)))
fitted.mod.HM <- BaumWelch(mod)
summary(fitted.mod.HM)

#nstate = 2 (stationary case)
Pi <- rbind(c(.8,.2),c(.1,.9))
fitted.mod.HM.stat <- dthmm(rainfall,Pi=Pi,delta=c(.5,.5),"pois",list(lambda=c(10,20)),nonstat=FALSE)
summary(fitted.mod.HM.stat)
BaumWelch(fitted.mod.HM.stat)

#RSS
library("ggplot2")
Residuals <- residuals(fitted.mod.HM)
RSS <- sum(Residuals^2)
mean(Residuals)
2*sqrt(var(Residuals))
Index <- c(1:75)
Index <- data.frame(Index)
df <- data.frame(Residuals,Index)
ggplot(df, aes(Index, Residuals)) +
  geom_point()+
  ggtitle("Two-state Poisson HMM residuals plot")+
  theme(panel.border = element_rect(color = "black",
                                  fill = NA,
                                  size = 1))+
  geom_hline(yintercept=2.084557,col = "red")+
  geom_hline(yintercept=-2.084557,col = "red")+
  geom_rect(aes(xmin = -Inf, xmax = Inf, ymin = 2.084557, ymax = Inf),
            fill = "pink", alpha = 0.01)+
  geom_rect(aes(xmin = -Inf, xmax = Inf, ymin = -Inf, ymax = -2.084557),
            fill = "pink", alpha = 0.01)+
  theme(plot.title = element_text(hjust = 0.5))

#nstate = 3 (non-stationary case)
Pi <- rbind(c(.8,.0,.7),c(.2,.0,.3),c(.0,1,.0))
mod <- dthmm(rainfall,Pi=Pi,delta=c(1/3,1/3,1/3),"pois", list(lambda=c(10,20,30)))
fitted.mod.HM <- BaumWelch(mod)
summary(fitted.mod.HM)

#nstate = 3 (stationary case)
Pi <- rbind(c(.0,.7,.3),c(.0,.8,.2),c(1,.0,.0))
fitted.mod.HM.stat <- dthmm(rainfall,Pi=Pi,delta=c(1/3,1/3,1/3),"pois",list(lambda=c(10,20,30)),nonstat=FALSE)
summary(fitted.mod.HM.stat)
BaumWelch(fitted.mod.HM.stat)

#RSS
Residuals <- residuals(fitted.mod.HM)
mean(Residuals)
RSS <- sum(Residuals^2)
RSS
2*sqrt(var(Residuals))
Index <- c(1:75)
Index <- data.frame(Index)
df <- data.frame(Residuals,Index)
ggplot(df, aes(Index, Residuals)) +
  geom_point()+
  ggtitle("Three-state Poisson HMM residuals plot")+
  theme(panel.border = element_rect(color = "black",
                                    fill = NA,
                                    size = 1))+
  geom_hline(yintercept=1.973902,col = "red")+
  geom_hline(yintercept=-1.973902,col = "red")+
  geom_rect(aes(xmin = -Inf, xmax = Inf, ymin = 1.973902, ymax = Inf),
            fill = "pink", alpha = 0.01)+
  geom_rect(aes(xmin = -Inf, xmax = Inf, ymin = -Inf, ymax = -1.973902),
            fill = "pink", alpha = 0.01)+
  theme(plot.title = element_text(hjust = 0.5))

#EM algorithm
#generate some Poisson mixture data
data <- c(rpois(100,2), rpois(100,10))

#run the ML-EM algorithm to learn the mixture model
library(PoissonMixR)
t1 <- EM_PMM_algo(rainfall,2,iter = 50)

#plot the EM objective function, should be monotonically increasing and monitors convergence
plot(t1$sum_of_rows_ln_sum,
     type = 'l',
     main = "convergence of EM objective function",
     bty = 'n')

#check the cluster assignments (using original data this is not a prediction, which can also be done)
cluster_indicator <- c()
for(i in 1:length(rainfall)){
  cluster_indicator <- c(cluster_indicator,which.max(t1$norm_phi[i,]))
}
plot(rainfall,cluster_indicator,
     pch = 16,
     bty = 'n')

"""# Fitting 2-state and 3-state HMM"""

#====================================== fit 2-state HMM
m<-2
lambda0<-c(15,25)
gamma0<-matrix(
  c(
  0.9,0.1,
  0.1,0.9
),m,m,byrow=TRUE)
mod2s<-pois.HMM.mle(x,m,lambda0,gamma0,stationary=TRUE)
delta0<-c(1,1)/2
mod2h<-pois.HMM.mle(x,m,lambda0,gamma0,delta=delta0,stationary=FALSE)
mod2s; mod2h

#====================================== fit 3-state HMM
m<-3
lambda0<-c(10,20,30)
gamma0<-matrix(
  c(
    0.8,0.1,0.1,
    0.1,0.8,0.1,
    0.1,0.1,0.8
  ),m,m,byrow=TRUE)
mod3s<-pois.HMM.mle(x,m,lambda0,gamma0,stationary=TRUE)
delta0 <- c(1,1,1)/3
mod3h<-pois.HMM.mle(x,m,lambda0,gamma0,delta=delta0,stationary=FALSE)
mod3s; mod3h

"""# State Prediction"""

#====================================== state prediction
pois.HMM.state_prediction <- function(h=1,x,mod){
  n <- length(x)
  la <- pois.HMM.lforward(x,mod)
  c <- max(la[,n])
  llk <- c+log(sum(exp(la[,n]-c)))
  statepreds <- matrix(NA,ncol=h,nrow=mod$m)
  foo <- exp(la[,n]-llk)
  for (i in 1:h){
    foo <- foo%*%mod$gamma
    statepreds[,i] <- foo
  }
  return(statepreds)
}

pois.HMM.state_prediction(50,x,mod3s)
pois.HMM.state_prediction(50,x,mod3h)

"""# Forecast Probabilities"""

#====================================== forecast probabilities
# note that the output 'dxf' is a matrix
pois.HMM.forecast <- function(xf,h=1,x,mod){
  n <- length(x)
  nxf <- length(xf)
  dxf <- matrix(0,nrow=h,ncol=nxf)
  foo <- mod$delta*dpois(x[1],mod$lambda)
  sumfoo <- sum(foo)
  lscale <- log(sumfoo)
  foo <- foo/sumfoo
  for (i in 2:n){
    foo <- foo%*%mod$gamma*dpois(x[i],mod$lambda)
    sumfoo <- sum(foo)
    lscale <- lscale+log(sumfoo)
    foo <- foo/sumfoo
  }
  for (i in 1:h){
    foo <- foo%*%mod$gamma
    for (j in 1:mod$m) dxf[i,] <- dxf[i,] + foo[j]*dpois(xf,mod$lambda[j])
  }
  return(dxf)
}


#=== use it for 1-step-ahead and plot the forecast distribution
h<-1
xf<-0:50
forecasts<-pois.HMM.forecast(xf,h,x,mod3s)
fc<-forecasts[1,]
par(mfrow=c(1,1),las=1)
plot(xf,fc,type="h",
     main=paste("Rainfall series: forecast distribution for", d[n]+1),
     xlim=c(0,max(xf)),ylim=c(0,0.12),xlab="count",ylab="probability",lwd=3)

#=== forecast 1-4 steps ahead and plot these
h<-4
xf<-0:45
forecasts<-pois.HMM.forecast(xf,h,x,mod3s)

par(mfrow=c(2,2),las=1)
for (i in 1:4){
  fc<-forecasts[i,]
  plot(xf,fc,type="h",main=paste("Forecast distribution for",d[n]+i),
       xlim=c(0,max(xf)),ylim=c(0,0.12),xlab="count",ylab="probability",lwd=3)
}

#=== Compute the marginal distribution for mod3h.
#=== This is also the long-term forecast.
m<-3
lambda<-mod3h$lambda
delta<-solve(t(diag(m)-mod3h$gamma+1),rep(1,m))
datat<-numeric(length(xf))
for (j in 1:m) datat <- datat + delta[j]*dpois(xf,lambda[j])

#=== Compare the 50-year ahead forecast with the long-term forecast.
h<-50
xf<-0:45
forecasts<-pois.HMM.forecast(xf,h,x,mod3h)
fc<-forecasts[h,]
par(mfrow=c(1,1),las=1)
plot(xf,fc,type="h",
     main=paste("Forecast distribution for", d[n]+h),
     xlim=c(0,max(xf)),ylim=c(0,0.12),xlab="count",ylab="probability",lwd=3)
lines(xf,datat,col="gray",lwd=3)