export default {
    title: 'Zero',
    description: 'Zero Documentation',
    // base : '/zero/',
    lastUpdated: true,
    lang: 'en-US',
    cleanUrls: true,

    markdown: {
      theme: 'material-theme-palenight',
      lineNumbers: true,
      anchors: {
        slugify(str) {
          return encodeURIComponent(str)
        }
      }
    },

    // Google Analytics
    // head: [
    //   [ 'script', { async: '' , src: "https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX" } ],
    //   [ 'script', {} , "window.dataLayer = window.dataLayer || [];\nfunction gtag(){dataLayer.push(arguments);}\ngtag('js', new Date());\ngtag('config', 'G-XXXXXXXXXX');" ],
    // ],

    themeConfig: {
      siteTitle: 'Zero',
      logo : '/logo.png',

      // DocSearch by Algolia
      // algolia: {
      //   appId: 'XXXXXXXXXXXX',
      //   apiKey: 'XXXXXXXXXXXXXXXXXXXX',
      //   indexName: 'XXXXX'
      // },

      editLink: {
        pattern: 'https://github.com/Ananto30/zero/tree/main/docs/:path',
        text: 'Edit this page on GitHub'
      },

      // Navigation Section
      nav: [
        { text: 'Home', link: '/' },
        { text: 'Documentation', link: 'getting_started/overview.md' },
      ],
      socialLinks: [
        { icon: 'github', link: 'https://github.com/Ananto30/zero' },
      ],

      // Sidebar Section
      sidebar: [

        {
          text: 'Getting Started',
          collapsed: false,
          items: [
            { text: 'Overview',link: 'getting_started/overview.md' },
            { text: 'About',link: 'getting_started/about.md' },
            { text: 'Benchmark',link: 'getting_started/benchmark.md' },
            { text: 'Install',link: 'getting_started/install.md' },
            { text: 'Uninstall',link: 'getting_started/uninstall.md' },
          ],
        },

        {
          text: 'Concepts',
          collapsed: true,
          items: [
            { text: 'Architecture',link: 'concept/architecture.md' },
            { text: 'Lifecycle',link: 'concept/lifecycle.md' },
          ],
        },

        {
          text: 'The Basics',
          collapsed: true,
          items: [
            { text: 'Routing',link: 'basic/routing.md' },
            { text: 'Request',link: 'basic/request.md' },
            { text: 'Response',link: 'basic/response.md' },
            { text: 'Middleware',link: 'basic/middleware.md' },
          ],
        },

        {
          text: 'Advanced',
          collapsed: true,
          items: [
            { text: 'Code Generation',link: 'advanced/code_generation.md' },
          ],
        },
        
        {
          text: 'Testing',
          collapsed: true,
          items: [
            { text: 'Getting Started',link: 'testing/getting_started.md' },
            { text: 'Http Testing',link: 'testing/http_testing.md' },
          ],
        },

        {
          text: 'Prologue',
          collapsed: true,
          items: [
            { text: 'Release Note',link: 'prologue/release_note.md' },
            { text: 'Upgrade Guide',link: 'prologue/upgrade_guide.md' },
            { text: 'Contribution Guide',link: 'prologue/contribution_guide.md' },
          ],
        },
        
      ],

      // Footer Section
      footer: {
        message: 'Released under the MIT License.',
        copyright: 'Copyright © 2023 zero'
      },
    },
  }