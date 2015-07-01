__author__ = 'jason'

import MySQLdb as mdb

class ConnectionClosed(Exception):
    def __init__(self):
        pass

class QueryInterface:
    def __init__(self):
        pass

    __connection = None;

    # CONNECTION MANAGEMENT

    def openConnection(self,hostname,username,password):
        self.__connection = mdb.connect(hostname,username,password,'MediaManagement',charset='utf8',use_unicode=True)
        pass

    def testConnection(self):
        if (self.__connection == None):
            return False;

        if (self.__connection.open == 0):
            return False

        return True

    def getCursor(self):
        if self.testConnection() == False:
            raise ConnectionClosed

        return self.__connection.cursor()

    def closeConnection(self):
        if self.testConnection() == True:
            self.__connection.close()
        self.__connection = None;

    # BASIC LOOKUP METHODS

    def getCampaignList(self):
        cursor = self.getCursor()

        query = """
            select * from Campaign
        """

        cursor.execute(query)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getCampaignFromName(self,campaignName):
        cursor = self.getCursor()

        query = """
            select * from Campaign where CampaignName = %s
        """

        cursor.execute(query,(campaignName,))

        data = cursor.fetchall()

        cursor.close()

        return data

    def getUsers(self,userIds):
        cursor = self.getCursor()

        query = """
            select
                *
            from
                User
            where
                id in (%s)
        """

        in_p = ', '.join(map(lambda x: '%s', userIds))
        query = query % in_p

        cursor.execute(query, userIds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getHashtags(self,hashtagIds):
        cursor = self.getCursor()

        query = """
            select
                *
            from
                Hashtag
            where
                id in (%s)
        """

        in_p = ', '.join(map(lambda x: '%s', hashtagIds))
        query = query % in_p

        cursor.execute(query, hashtagIds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getUserIdFromTwitterName(self,twitterName):
        cursor = self.getCursor()

        query = """
            select
                id
            from
                User
            where
                TwitterName = %s
        """

        cursor.execute(query,(twitterName,))

        data = cursor.fetchone()

        if data is not None:
            return data[0]
        else:
            return None

    def getLinks(self,linkIds):
        cursor = self.getCursor()

        query = """
            select
                *
            from
                Link
            where
                id in (%s)
        """

        in_p = ', '.join(map(lambda x: '%s', linkIds))
        query = query % in_p

        cursor.execute(query, linkIds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getPlatforms(self,platformIds):
        cursor = self.getCursor()

        query = """
            select
                *
            from
                Platform
            where
                id in (%s)
        """

        in_p = ', '.join(map(lambda x: '%s', platformIds))
        query = query % in_p

        cursor.execute(query, platformIds)

        data = cursor.fetchall()

        cursor.close()

        return data


    ### These Queries run over the normalized schema and are not delayed

    # Get the TopN Hashtags including the Campaign Hashtags
    def getTopHashtags(self,numResults,startTime,endTime,campaignId):
        cursor = self.getCursor()

        query = """
            select
                Hashtag.Hashtag Hashtag,
                sum(HashtagCount.Count) Total
            from
                HashtagCount
                left join Hashtag on
                    HashtagCount.HashtagId = Hashtag.id
            where
                HashtagCount.StartTime >= %s
                and HashtagCount.StartTime <= %s
                and HashtagCount.CampaignId = %s
            group by
                Hashtag
            order by
                Total desc
            limit
                %s;
        """

        cursor.execute(query,(startTime,endTime,campaignId,numResults))

        data = cursor.fetchall()

        cursor.close()

        return data

    # Get the TopN Hashtags NOT including the Campaign Hashtags
    def getOtherTopHashtags(self,numResults,startTime,endTime,campaignId,sinceCampaignStart=False):
        cursor = self.getCursor()

        query = """
            select
                Hashtag.Hashtag Hashtag,
                CampaignHashtag.Hashtag,
                sum(HashtagCount.Count) Total
            from
                HashtagCount
                left join Hashtag on
                    HashtagCount.HashtagId = Hashtag.id
                left join Campaign on
                    HashtagCount.CampaignId = Campaign.id
                left join CampaignToHashtag on
                    Campaign.id = CampaignToHashtag.CampaignId
                left join Hashtag as CampaignHashtag on
                    CampaignToHashtag.HashtagId = CampaignHashtag.id
                    and CampaignHashtag.Hashtag = Hashtag.Hashtag
            where
                HashtagCount.StartTime >= %s
                and HashtagCount.StartTime <= %s
                and CampaignHashtag.Hashtag is null
                and HashtagCount.CampaignId = %s
            group by
                Hashtag.Hashtag,
                CampaignHashtag.Hashtag
            order by
                Total desc
            limit
                %s;
        """

        cursor.execute(query,(startTime,endTime,campaignId,numResults))

        data = cursor.fetchall()

        cursor.close()

        return data

    # Get the TopN Links seen during the timeframe
    def getTopLinks(self,numResults,startTime,endTime,campaignId,shortURLs=True):
        cursor = self.getCursor()

        if shortURLs == True:
            linkField = "Link.LinkURL"
        else:
            linkField = "Link.ExpandedURL"

        query = """
            select
                {},
                sum(LinkCount.Count) Total
            from
                LinkCount
                left join Link on
                    LinkCount.LinkId = Link.id
            where
                LinkCount.StartTime >= %s
                and LinkCount.StartTime <= %s
                and LinkCount.CampaignId = %s
            group by
                {}
            order by
                Total desc
            limit
                %s;
        """.format(linkField,linkField)

        cursor.execute(query,(startTime,endTime,campaignId,numResults))

        data = cursor.fetchall()

        cursor.close()

        return data

    # Get the TopN most influential users by Mentions during the timeframe
    def getTopUsersByMentions(self,numResults,startTime,endTime,campaignId):
        cursor = self.getCursor()

        query = """
            select
                User.TwitterName,
                sum(MentionCount.Count) Total
            from
                MentionCount
                left join User on
                    MentionCount.UserId = User.id
            where
                MentionCount.StartTime >= %s
                and MentionCount.StartTime <= %s
                and MentionCount.CampaignId = %s
            group by
                User.TwitterName
            order by
                Total desc
            limit
                %s;
        """

        cursor.execute(query,(startTime,endTime,campaignId,numResults))

        data = cursor.fetchall()

        cursor.close()

        return data

    # Get the TopN most influential users by Retweets during the timeframe
    def getTopUsersByRetweets(self,numResults,startTime,endTime,campaignId):
        cursor = self.getCursor()

        query = """
            select
                User.TwitterName,
                sum(RetweetCount.Count) Total
            from
                RetweetCount
                left join User on
                    RetweetCount.UserId = User.id
            where
                RetweetCount.StartTime >= %s
                and RetweetCount.StartTime <= %s
                and RetweetCount.CampaignId = %s
            group by
                User.TwitterName
            order by
                Total desc
            limit
                %s;
        """

        cursor.execute(query,(startTime,endTime,campaignId,numResults))

        data = cursor.fetchall()

        cursor.close()

        return data

    # Get the TopN most influential users by Mentions and Retweets during the timeframe
    def getTopUsersByRetweetsAndMentions(self,numResults,startTime,endTime,campaignId):
        cursor = self.getCursor()

        query = """
            select
                User.TwitterName,
                sum(Count) Total
            from
                (
                    (select
                        MentionCount.UserId,
                        MentionCount.Count
                    from
                        MentionCount
                    where
                        MentionCount.StartTime >= %s
                        and MentionCount.StartTime <= %s
                        and MentionCount.CampaignId = %s)
                    UNION ALL
                    (select
                        RetweetCount.UserId,
                        RetweetCount.Count
                    from
                        RetweetCount
                    where
                        RetweetCount.StartTime >= %s
                        and RetweetCount.StartTime <= %s
                        and RetweetCount.CampaignId = %s)
                ) Stuff
                left join User on
                    Stuff.UserId = User.id
            group by UserId
            order by Total desc
            limit %s;
        """

        cursor.execute(query,(startTime,endTime,campaignId,startTime,endTime,campaignId,numResults))

        data = cursor.fetchall()

        cursor.close()

        return data

    # Get the number of retweets and mentions for a user over a given timeframe

    # Get the TopN most influential users by Timeline Deliveries during the timeframe
    def getTopTimelineDeliveries(self,numResults,startTime,endTime,campaignId):
        cursor = self.getCursor()

        query = """
            select
                User.TwitterName,
                sum(TimelineCount.Count) Total
            from
                TimelineCount
                left join User on
                    TimelineCount.UserId = User.id
            where
                TimelineCount.StartTime >= %s
                and TimelineCount.StartTime <= %s
                and TimelineCount.CampaignId = %s
            group by
                User.TwitterName
            order by
                Total desc
            limit
                %s;
        """

        cursor.execute(query,(startTime,endTime,campaignId,numResults))

        data = cursor.fetchall()

        cursor.close()

        return data

    # Get the number of timeline deliveries for a user over a given timeframe

    # Get the TopN  platforms over a given timeframe
    def getTopPlatforms(self,numResults,startTime,endTime,campaignId):
        cursor = self.getCursor()

        query = """
            select
                Platform.PlatformShort,
                sum(PlatformCount.Count) Total
            from
                PlatformCount
                left join Platform on
                    PlatformCount.PlatformId = Platform.id
            where
                PlatformCount.StartTime >= %s
                and PlatformCount.StartTime <= %s
                and PlatformCount.CampaignId = %s
            group by
                Platform.PlatformShort
            order by
                Total desc
            limit
                %s;
        """

        cursor.execute(query,(startTime,endTime,campaignId,numResults))

        data = cursor.fetchall()

        cursor.close()

        return data

    # Sort the 24 hours of the day by their popularity (using TweetCount) over the given
    # timeframe
    def getPopularHour(self,startTime,endTime,campaignId,sort=False):
        cursor = self.getCursor()

        query = """
            select
                HOUR(StartTime) as "Hour",
                SUM(Count) as "Total"
            from
                TweetCount
            where
                TweetCount.StartTime >= %s
                and TweetCount.StartTime <= %s
                and TweetCount.CampaignId = %s
            group by
                Hour(StartTime)
        """

        if sort == True:
            query += """
                order by
                    SUM(Count) desc;
            """

        cursor.execute(query,(startTime,endTime,campaignId))

        data = cursor.fetchall()

        cursor.close()

        return data

    ### These queries use the cached data that is generated every hour and stored in the
    ### data warehouse

    # Get TopN Hashtags since teh Campaign Started.
    # If endTime is specified it will be used instead of getting the most recent store value
    # If recent is not zero, multiple rows will be returned sorted such that the first row is the most recent
    def getTopHashtagsSinceCampaignStart(self,campaignId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    HashtagHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,recent)
        else:
            query = """
                select
                    *
                from
                    HashtagHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                    and EndTime <= %s
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

    # Get a history of tweets per hour since campaign start.
    # If endTime is specified it will be used instead of getting the most recent store value
    # If recent is not zero, multiple rows will be returned sorted such that the first row is the most recent
    def getCumulativeTweetsSinceCampaignStart(self,campaignId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    TweetHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,recent)
        else:
            query = """
                select
                    *
                from
                    TweetHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                    and EndTime <= %s
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

        # Get a history of tweets per hour since campaign start.

    # If endTime is specified it will be used instead of getting the most recent store value
    # If recent is not zero, multiple rows will be returned sorted such that the first row is the most recent
    def getInstantaneousTweetsSinceCampaignStart(self,campaignId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    TweetCount
                where
                    CampaignId = %s
                order by
                    StartTime desc
                limit
                    %s
            """

            binds = (campaignId,recent)
        else:
            query = """
                select
                    *
                from
                    TweetCount
                where
                    CampaignId = %s
                    and StartTime <= %s
                order by
                    StartTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getInstantaneousTimelineDeliveriesSinceCampaignStart(self,campaignId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    TimelineCountTotal
                where
                    CampaignId = %s
                order by
                    StartTime desc
                limit
                    %s
            """

            binds = (campaignId,recent)
        else:
            query = """
                select
                    *
                from
                    TimelineCountTotal
                where
                    CampaignId = %s
                    and StartTime <= %s
                order by
                    StartTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

    # Get a history of mentions for a particular user per hour since campaign start.
    # If endTime is specified it will be used instead of getting the most recent store value
    # If recent is not zero, multiple rows will be returned sorted such that the first row is the most recent
    def getUserMentionsSinceCampaignStart(self,campaignId,userId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    MentionHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                    and UserId = %s
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,userId,recent)
        else:
            query = """
                select
                    *
                from
                    MentionHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                    and EndTime <= %s
                    and UserId = %s
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,userId,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getTopPlatformsSinceCampaignStart(self,campaignId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    PlatformHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,recent)
        else:
            query = """
                select
                    *
                from
                    PlatformHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                    and EndTime <= %s
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getTopLinksSinceCampaignStart(self,campaignId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    LinkHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,recent)
        else:
            query = """
                select
                    *
                from
                    LinkHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                    and EndTime <= %s
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getTopInfluencersMRSinceCampaignStart(self,campaignId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    InfluenceMRHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,recent)
        else:
            query = """
                select
                    *
                from
                    InfluenceMRHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                    and EndTime <= %s
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getTopInfluencersRSinceCampaignStart(self,campaignId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    InfluenceRHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,recent)
        else:
            query = """
                select
                    *
                from
                    InfluenceRHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                    and EndTime <= %s
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getTopUsersTimelineDeliveriesSinceCampaignStart(self,campaignId,recent=0,endTime=None):
        cursor = self.getCursor()

        if recent <= 0:
            recent = 1
        else:
            recent += 1

        if endTime == None:
            query = """
                select
                    *
                from
                    TimelineHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,recent)
        else:
            query = """
                select
                    *
                from
                    TimelineHourTotals
                where
                    CampaignId = %s
                    and SinceCampaignStart = 1
                    and EndTime <= %s
                order by
                    EndTime desc
                limit
                    %s
            """

            binds = (campaignId,endTime,recent)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data

    def getPopularHourSinceCampaignStart(self,campaignId,endTime=None):
        cursor = self.getCursor()

        query = """
            select
                min(StartTime)
            from
                TweetCount
            where
                CampaignId = %s;
        """

        binds = (campaignId,)

        cursor.execute(query,binds)

        startTime = cursor.fetchone()[0]

        if endTime == None:
            query = """
                select
                    max(StartTime)
                from
                    TweetCount
                where
                    CampaignId = %s;
            """

            binds = (campaignId,)

            cursor.execute(query,binds)

            endTime = cursor.fetchone()[0]

        cursor.close()

        return self.getPopularHour(startTime,endTime,campaignId)

    def getTweetCountsPerHourSinceCampaignStart(self,campaignId,endTime=None):
        cursor = self.getCursor()

        if endTime == None:
            query = """
                select
                    date_format(StartTime, '%%Y-%%m-%%d %%H:00:00') "Hour",
                    sum(Count) "Count"
                from
                    TweetCount
                where
                    CampaignId = %s
                group by
                    date_format(StartTime, '%%Y-%%m-%%d %%H:00:00')
                order by
                    date_format(StartTime, '%%Y-%%m-%%d %%H:00:00') desc;
            """

            binds = (campaignId,)
        else:
            query = """
                select
                    date_format(StartTime, '%%Y-%%m-%%d %%H:00:00') "Hour",
                    sum(Count) "Count"
                from
                    TweetCount
                where
                    StartTime <= %s
                    and CampaignId = %s
                group by
                    date_format(StartTime, '%%Y-%%m-%%d %%H:00:00')
                order by
                    date_format(StartTime, '%%Y-%%m-%%d %%H:00:00') desc;
            """

            binds = (campaignId,endTime)

        cursor.execute(query,binds)

        data = cursor.fetchall()

        cursor.close()

        return data
