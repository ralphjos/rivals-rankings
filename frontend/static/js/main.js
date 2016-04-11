var navView = new NavView();

// Build application router
var AppRouter = Backbone.Router.extend({
  routes: {
    "": "rankings",
    "rankings/:region": "rankings"
  },
  home: function(){
    var homeView = new HomeView();
  },

  // Initialize rankingView and currentRanks model
  rankings: function(region){
    var currentRanks;
    if (!region) {
        currentRanks = new Rankings({region: "national"});
    } else {
        currentRanks = new Rankings({region: region});
    }

    var rankingView = new RankingView({model: currentRanks});
    // Fetch ranking data and update views accordingly
    currentRanks.fetch({
      success: function() {
        rankingView.render()
      },
      error: function() {
        rankingView.renderFailure()
      }
    });
  }

});


// Initiate the router
var app_router = new AppRouter;
Backbone.history.start()
