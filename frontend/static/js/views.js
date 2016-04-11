var NavView = Backbone.View.extend({
  el: '#nav',

  initialize: function(){
    this.render();
  },

  render: function(){
    var navPointer = this;
    $.get('frontend/templates/navbar.html', function(navbarTemplate){
      navPointer.$el.html(navbarTemplate);
    });
    return this;
  },
});

var RankingView = Backbone.View.extend({
  el: '#container',

  initialize: function(){
  },

  render: function(){
    var rankingPointer = this;
    $.get('frontend/templates/rankings.html', function(rankingsTemplate){
      // Compile handlebar template with the rankings.html template
      var template = Handlebars.compile(rankingsTemplate);
      // Pass our data to the template
      var compiledHtml = template(rankingPointer.model.attributes);
      // Set element to newly compiled template
      rankingPointer.$el.html(compiledHtml);
    });
    return this;
  },

  renderFailure: function(){
    this.$el.html('<p>Failed to retrieve data from API.</p>');
    return this;
  }
});