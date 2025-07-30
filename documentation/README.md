# Documentation Guide

This documentation template has been built with [vitepress](https://vitepress.dev)

Use this extention while writing documentation : [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)

## Steps

Step 1: Clone the repository

```bash
git clone git@github.com:Ananto30/zero.git
```

Step 2: Move terminal inside documentation directory

```bash
cd documentation
```

Step 3: Install npm dependencies (your device should already have npm installed)

```bash
npm install
```

Step 4: Run the documentation site on browser for development

```bash
npm run docs:dev
```

Step 5: build website to publish

```bash
npm run docs:build
```

This command will create website files inside `documentation/docs/.vitepress/dist` directory. Inside `dist` directory generated website files will be avaliable.

Step 6 : preview the site locally before publishing.

```bash
npm run docs:preview
```

If everything is good, you can publish the website using the files existing inside `dist` directory.
