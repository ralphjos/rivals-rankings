// Build application router
var AppRouter = Backbone.Router.extend({
  routes: {
    "": "rankings",
    "rankings": "rankings"
  },
  home: function(){
    var homeView = new HomeView();
  },

  // Initialize rankingView and currentRanks model
  rankings: function(){
    var currentRanks = new Rankings();
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
