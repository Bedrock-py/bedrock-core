## Experiment processing file, re-factored to batch process multiple games.
## Created by Pablo Diego Rosell, PhD, for Gallup inc. in October 2018
## For any questions, contact pablo_diego-rosell@gallup.co.uk

# clear workspace
URL <- 'https://volunteerscience.com/gallup/boomtown_metadata'

# define constants
gamedata_names <- c("matchid", "round", "h1.1", "h1.3", "h2.1", "h2.2", "h2.3",
                    "h2.4", "h2.5", "h2.6", "h3.2", "h3.3", "h3.4", "h3.5",
                    "tools", "innovation", "CSE", "leaderChoice", "nConnected")
str1.1 <- c("None", "Weak", "Normal", "Strong")
str2.1 <- c("False", "True")
str3.2 <- c("LowTolerance", "HighTolerance")
str3.3 <- c("highStatus_highLegitimacy", "highStatus_lowLegitimacy",
            "lowStatus_highLegitimacy", "lowStatus_lowLegitimacy")
str3.4 <- c("LowTransformational", "HighTransformational")

tool_dict <- list(
    'TNTbarrel,SatchelCharge' = 1,
    'BlackPowder,Dynamite' = 2,
    'BlackPowder,RDX' = 3,
    'RDX,Dynamite' = 4,
    'Mine1,Mine2' = 5,
    'Mine4,Mine3' = 6,
    'Mine1,BlackPowder' = 7,
    'Mine2,BlackPowder' = 7,
    'Mine3,BlackPowder' = 8,
    'Mine4,BlackPowder' = 8,
    'TNTbarrel,Dynamite' = 9,
    'BlackPowder,SatchelCharge' = 10,
    'SatchelCharge,RDX' = 11,
    'Dynamite,SatchelCharge' = 12
)

# define functions
# helper function for grepping in h_values_complex
get_search_value <- function(tools, value) {
    return(paste(names(which(tools == value)), collapse = '|'))
}

# gets various h values, given input parameters for parsing
h_values <- function(data, h, rds) {
    tmp <- lapply(data, function(x) c(0:(length(h)-1))[sapply(h, grepl, x)])
    return(mapply(function(x, n) {
        rep(x, n)
    }, tmp, rds, SIMPLIFY = FALSE))
}

# gets other h values that are complex, based on multiple conditions
h_values_complex <- function(rounds, tool_choices, tool_set, v1, v2) {
    return(mapply(function(rds, tools) {
        tmp <- rep(NA, rds)
        tmp[grep(get_search_value(tool_set, v1), tools)] <- 0
        tmp[grep(get_search_value(tool_set, v2), tools)] <- 1
        return(tmp)
    }, rounds, tool_choices, SIMPLIFY = FALSE))
}

# Read in logs
files <- list.files(dd, pattern = "*.txt")
datalist <- lapply(files[!(files %in% 'cookies.txt')], function(x) {
    readLines(paste(dd, x, sep = '/'))
})

# LeaderSelection events before game suspended
leaderSelectionAll <- lapply(datalist, function(x) x[grep("LeaderSelection|GameSuspended", x)])
leaderSelection <- lapply(leaderSelectionAll,
                          function(x) if ('TRUE' %in% grepl("GameSuspended", x)) {
                            x[0:(grep("GameSuspended", x)-1)]
                          } else {
                            x
                          })
leaderSelectionYes <- lapply(leaderSelection, function(x) length(as.character(x))>0 & length(as.character(x))<14)

# Identify games played during fielding period (StartMatch date >= 10/25/2018)
StartMatch <- lapply(datalist, function(x) gsub(" .*$", "", x[grep("StartMatch", x)]))
dates <- lapply(StartMatch, function(x) as.Date((gsub("StartMatch,", "", x)), "%m/%d/%Y"))
datesFIELD <- lapply(dates, function(x) x >= as.Date('2018-10-25'))

# Subset datalist according to the two conditions above:
# 1. Had at least one "LeaderSelection") event before the game was suspended
# 2. Played during fielding period (StartMatch date >= 10/25/2018)
datalist<-datalist[leaderSelectionYes==TRUE & datesFIELD==TRUE]

# Count number of games
nElements <- length(datalist)

# Count number of rounds (leaderSelection events)
leaderVotes <- lapply(datalist, function(x) x[grep("LeaderSelection", x)])
nRounds <- lapply(leaderVotes, function(x) length(x))

# Extract choices in the shop
toolChoicesAll <- lapply(datalist, function(x) x[grep("StartVotation", x)])
toolChoices <- mapply(function(x,y) {return(x[1:y])}, x=toolChoicesAll, y=nRounds)

# Extract match id to create group variable
matchid <- lapply(datalist, function(x) x[grep("StartMatch", x)])
matchid <- lapply(matchid, function(x) as.numeric(strsplit(x,',',fixed=TRUE)[[1]][3]))
matchid <- mapply(function(x, n) {
    rep(x, n)
}, matchid, nRounds, SIMPLIFY = FALSE)

# Count number of connected players
PlayerConnection <- lapply(datalist, function(x) length(x[grep("PlayerConnection", x)]))
PlayerConnections <- mapply(function(nConnected, n) {
  return(rep(nConnected, n))
}, PlayerConnection, nRounds, SIMPLIFY = FALSE)

# Extract values for block-randomized hypotheses
gameSettings <- lapply(datalist, function(x) x[grep("SetupMatch", x)])

# get h values
h1.1 <- h_values(gameSettings, str1.1, nRounds)
h2.1 <- h_values(gameSettings, str2.1, nRounds)
h3.2 <- h_values(gameSettings, str3.2, nRounds)
h3.3 <- h_values(gameSettings, str3.3, nRounds)
h3.4 <- h_values(gameSettings, str3.4, nRounds)

# Assign values of h1.3 (Fixed at Rounds 4 & 9 = 1, Rounds = 5 & 7 = 2, else = 0)
h1.3Fixed <-rep(list(c(0, 0, 0, 1, 2, 0, 2, 0, 1, 0, 0, 0, 0)), nElements)
h1.3 <- mapply(function(x,y) {return(x[1:y])}, x=h1.3Fixed, y=nRounds)


# Assign values of h3.5 (Fixed at Round 1 = 0, Rounds 6, 8 = 2, else = 1)
h3.5Fixed <- rep(list(c(0, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1)), nElements)
h3.5 <- mapply(function(x,y) {return(x[1:y])}, x=h3.5Fixed, y=nRounds)

# Extract value of tool choice for each round
tools <- lapply(toolChoices, function(x) {
    tmp <- lapply(x, function(y) {
        do.call(c,
            tool_dict[do.call(c,
                lapply(names(tool_dict), function(z) {
                    grepl(z, y)
                })
            )]
        )
    })
    return(do.call(c, lapply(tmp, function(y) {
        ifelse(!is.null(y), y, NA)
    })))
})

# Assign hypothesis and hypothesis level by round, based on tool choices
h2.2 <- h_values_complex(nRounds, toolChoices, tool_dict, 1, 2)
h2.3 <- h_values_complex(nRounds, toolChoices, tool_dict, 1, 3)
h2.4 <- h_values_complex(nRounds, toolChoices, tool_dict, 4, 1)
h2.5 <- h_values_complex(nRounds, toolChoices, tool_dict, 5, 6)
h2.6 <- h_values_complex(nRounds, toolChoices, tool_dict, 7, 8)
control1 <- h_values_complex(nRounds, toolChoices, tool_dict, 9, 10)
control2 <- h_values_complex(nRounds, toolChoices, tool_dict, 11, 12)

# Extract innovation outcome, based on tool choice.
leaderChoice <- lapply(leaderVotes, function(x) strsplit(x, ',', fixed = TRUE))
leaderChoice <- lapply(leaderChoice, function(x) sapply(x, "[[", 3))

innovation <- mapply(function(leader, tool) {
    tmp <- ifelse(
        (grepl(names(tool_dict[1]), tool) == TRUE & grepl('SatchelCharge', leader) == TRUE) |
        (grepl(names(tool_dict[2]), tool) == TRUE & grepl('Dynamite', leader) == TRUE) |
        (grepl(names(tool_dict[3]), tool) == TRUE & grepl('RDX', leader) == TRUE) |
        (grepl(names(tool_dict[4]), tool) == TRUE & grepl('RDX', leader) == TRUE) |
        (grepl(names(tool_dict[5]), tool) == TRUE & grepl('Mine2', leader) == TRUE) |
        (grepl(names(tool_dict[6]), tool) == TRUE & grepl('Mine4', leader) == TRUE) |
        (grepl(names(tool_dict[7]), tool) == TRUE & grepl('Mine1', leader) == TRUE) |
        (grepl(names(tool_dict[9]), tool) == TRUE & grepl('Mine3', leader) == TRUE) |
        (grepl(names(tool_dict[8]), tool) == TRUE & grepl('Mine2', leader) == TRUE) |
        (grepl(names(tool_dict[10]), tool) == TRUE & grepl('Mine4', leader) == TRUE), 1,
        ifelse(
            grepl(names(tool_dict[11]), tool) == TRUE |
            grepl(names(tool_dict[12]), tool) == TRUE |
            grepl(names(tool_dict[13]), tool) == TRUE |
            grepl(names(tool_dict[14]), tool) == TRUE, NA, 0
        )
    )
    return(tmp)
}, leaderVotes, toolChoices, SIMPLIFY = FALSE)

# Post-game survey
survey <- lapply(datalist, function(x) x[grep("SurveyResponse", x)])
survey <- lapply(survey, function(x) strsplit(x,',',fixed=TRUE))
playerID <- lapply(survey, function(x) sapply(x, "[[", 3))
surveyQuestions<-lapply(survey, function(x) sapply(x, "[[", 4))
surveyResponses<-lapply(survey, function(x) sapply(x, "[[", 5))

CSE <- lapply(surveyResponses, function(x) mean(as.numeric(as.character(x))))
CSE <- mapply(function(cse, n) {
    return(rep(cse, n))
}, CSE, nRounds, SIMPLIFY = FALSE)

# Merge all variables into a single frame
gamesList <- list(
    matchid,
    lapply(nRounds, function(x) {return(1:x)}),
    h1.1,
    h1.3,
    h2.1,
    h2.2,
    h2.3,
    h2.4,
    h2.5,
    h2.6,
    h3.2,
    h3.3,
    h3.4,
    h3.5,
    tools,
    innovation,
    CSE,
    leaderChoice,
    PlayerConnections
)

# run a check on gamesList to ensure the flattening to a matrix/data frame
# works out okay
gamesList <- lapply(gamesList, function(x) {
    tmp <- mapply(function(y, z) {
        if(length(y) == 0) {
            return(rep(NA, z))
        } else {
            return(y)
        }
    }, x, nRounds, SIMPLIFY = FALSE)
    return(tmp)
})

gamesData <- as.data.frame(matrix(unlist(gamesList), nrow = sum(unlist(nRounds))))
colnames(gamesData) <- gamedata_names

gamesData$h3.3<-as.numeric(gamesData$h3.3)
gamesData$h3.3[gamesData$h1.1==0] <- 9
gamesData$h3.3<-as.factor(gamesData$h3.3)

# Load metadata
# Downloads automatically when visting this URL https://volunteerscience.com/gallup/boomtown_metadata/
# Tried to automatize download process using "download.file" command, but not working properly.
# Copy and paste "boomtown_metadata.csv" from "downloads" folder to working directory, then execute below.


    metadata <- readLines(paste(dd, 'boomtown_metadata.csv', sep = '/'))

    metadata_names <- strsplit(metadata[1], ',')[[1]]
    metadata <-  as.data.frame(do.call(rbind, strsplit(metadata, ',')[2:length(metadata)]),
                               stringsAsFactors = FALSE)
    names(metadata) <- metadata_names

    metadata$h3.1 <- ifelse(metadata$group == 'Ambiguity Low', 0, 1)
    gamesData  <-  merge(gamesData, metadata[, c('matchID',
                                               'h3.1',
                                               'date/time',
                                               'replay',
                                               'consumableKey',
                                               'settingsNum')],
                         by.x = "matchid", by.y = "matchID", all.x = TRUE)
    gamesData <- subset(gamesData, consumableKey != "boomtown_demo")
    write.csv(gamesData, file = paste(od, 'gamesData.csv', sep = '/'),
              row.names = FALSE)

