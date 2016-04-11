var Rankings = Backbone.Model.extend({
  url: function() {
    return '/rankings/' + this.attributes.region;
  }
});

var AllPlayers = Backbone.Model.extend({
  url: '/players'
});
